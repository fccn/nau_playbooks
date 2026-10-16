# ClickHouse partner resource-governance analysis

Scalability/performance-impact analysis behind `templates/partner_resource_limits.sql.j2`'s
default values, done for [fccn/nau-technical#981](https://github.com/fccn/nau-technical/issues/981).
Everything below is either a **hard fact** queried directly from live infrastructure, an
**existing accepted precedent** already running in this stack, or an explicitly labeled
**engineering judgment call**.

## The gap this closes

ClickHouse's existing `readonly` profile (`nau_playbooks/roles/clickhouse_docker_deploy/templates/users/user_config.xml`)
contains only `readonly=1` -- no `max_memory_usage`, `max_execution_time`, `max_threads`, or
quota. Confirmed live (via `system.settings_profile_elements`) that both dev and prod match
this exactly. Prod's existing "default" quota also has **all-NULL limits** (fully
unconstrained) -- this is a system-wide gap, not something specific to partner access, but
it's the thing partner access would be the first to actually expose to an external, less-trusted
caller.

## Hard facts (queried live, not estimated)

**Dev** (`clickhouse01-dev`, single node, no cluster):
- 4 cores, 8.3 GiB RAM total, `max_server_memory_usage` ≈ 7.49 GiB (ClickHouse's own 90%-of-RAM
  convention)

**Prod** (`clickhouse02/03/04-prd`, 3-node replicated `logs_cluster`, single shard):
- 16 cores/node, 32 GiB RAM/node, `max_server_memory_usage` ≈ 28.2 GiB/node
- Single shard (`internal_replication=1`, `shard_num=1`) → **no cross-node query parallelism**;
  any one query runs entirely on whichever replica the VIP routes it to
- Steady-state resident memory ~12.3 GiB across 11 concurrent processes observed live
- Largest ARTE-accessible table, `xapi.xapi_events_all_parsed`: 43.3 GiB / 366M rows
- Confirmed via `system.tables` that both `xapi.xapi_events_all_parsed` and
  `xapi.enrollment_events` have **`org` as the leading column in their sorting key** and are
  monthly-partitioned (`toYYYYMM(emission_time)`) -- so the `ROW POLICY`'s `org = 'AMA'` filter
  gets genuine primary-index pruning, not a full-table scan. This meaningfully reduces (but
  doesn't eliminate) risk: an org-filtered query can still scan that org's *entire* history
  across all partitions.

## Existing precedents already accepted in this stack

- Trino's own `resource-groups.json` "partners" subgroup (already reviewed/accepted for ARTE):
  `hardConcurrencyLimit: 5`, `softConcurrencyLimit: 3`, `maxQueued: 50`, `softMemoryLimit: 15%`.
- Trino's own global `query.max-memory-per-node = 2GB` (dev and prod) -- an already-accepted
  per-node, per-query budget for any catalog in this stack, including the `clickhouse_partners`
  catalog ARTE actually queries through.
- Trino's own global `query.max-execution-time = 10m` / `query.max-run-time = 15m`.
- ClickHouse's own existing (if unconfigured) "default" quota already uses a 1-hour rolling
  interval convention.

## Synthetic load test (dev, fully reverted afterward)

Built a disposable table (`loadtest_synthetic.synth_events`) mirroring `xapi_events_all_parsed`'s
real shape -- same column types, `ORDER BY (org, course_id, verb_id, actor_id, emission_time,
event_id)`, monthly partitioned, `randomPrintableASCII`-based payload for realistic
(non-trivially-compressible) storage, all tagged `org = 'AMA'` to simulate a worst-case
single-org slice. Granted `org_user_arte` `SELECT` on this table only, then ran a deliberately
expensive query (`GROUP BY actor_id, course_id` -- up to tens of millions of distinct group
keys -- plus `ORDER BY`, `uniqExact`, `avg(length(event))`) with and without the proposed
profile attached, at two different data sizes:

| Rows | Disk size | Uncapped (today's `readonly` profile) | Capped (`partner_readonly`: 2GB / 60s / 4 threads) |
|---|---|---|---|
| 20M | 10.3 GiB | Succeeded: peak_mem 1.54 GiB, duration 16.8s, read 12.06 GiB | Succeeded (under both caps) |
| 50M | 25.75 GiB | Succeeded: peak_mem 3.28 GiB, duration 44.9s, read 30.15 GiB | Killed: `Code: 241 MEMORY_LIMIT_EXCEEDED` at 1.86 GiB, 17s |

This confirms both halves of the goal: the cap doesn't break a normal/legitimate heavy query
(20M-row case has comfortable headroom), and it does actually trigger and stop an outsized one
(50M-row case) well before it could threaten node memory.

One implementation gotcha found during this test, relevant to why the role attaches the
profile/quota at the **role** level (`org_role_<partner>`) rather than per-user:
`CREATE SETTINGS PROFILE ... TO <role>` attaches to the role, and `ALTER USER ... SETTINGS
PROFILE` only changes the user's own default -- it does not override a profile already attached
to the user's role. Role-level attachment is the more durable, harder-to-accidentally-bypass
option, which is why the template targets `org_role_<partner>`, not `org_user_<partner>`.

All dev-side test artifacts (`loadtest_synthetic` database, the test grant, and the ad-hoc
`partner_readonly`/`partner_quota` objects created for this test) were fully dropped/reverted
afterward and confirmed back to baseline via `SHOW CREATE USER`, `SHOW GRANTS`,
`system.settings_profiles`, and `system.quotas`.

## Per-setting derivation (fact vs. judgment call)

| Setting | Value | Basis |
|---|---|---|
| `max_memory_usage` | 2 GB | **Precedent**: identical to Trino's existing `query.max-memory-per-node`. On a prod node (28.2 GiB server limit), 2GB × Trino's 5-concurrent-query cap for ARTE = 10GB worst case ≈ 35% of the server limit, leaving ~18GB of margin. Per-query; enforced for any connection, Trino or direct. |
| `max_memory_usage_for_user` | 10 GB | **Precedent, extended**: this is the same 5 × 2GB budget as above, but as a per-*user* ceiling, not just per-query. Added because `max_memory_usage` alone only bounds one query at a time -- a partner connecting to ClickHouse directly (bypassing Trino) isn't bound by Trino's 5-concurrent-query cap, so without this, nothing stops e.g. 20 parallel direct connections from using up to ~40GB against a 28.2GiB server limit, the exact scenario this PR sets out to prevent. Confirmed live this is a genuine per-user *aggregate* ceiling (ClickHouse's own error is "User memory limit exceeded", distinct from and independent of the per-query `max_memory_usage` error) -- so it isn't widened by the `max_concurrent_queries_for_user` figure below, which only bounds query *count*. |
| `max_concurrent_queries_for_user` | 40 | **Measured, not just precedent-derived**: Trino's own `hardConcurrencyLimit: 5` for ARTE multiplied by a real measured factor, not assumed 1:1. Inspected dev's `system.query_log` for actual traffic from Trino's ClickHouse JDBC connector (the real `clickhouse_partners` catalog, confirmed via `http_user_agent` containing `ClickHouse-JdbcDriver`) and found every single logical Trino-level query against this catalog issues ~6-8 ClickHouse statements, not 1 -- JDBC metadata-discovery calls (`currentUser()`, table/column listing) bracketing the actual data query. One representative burst: 33 metadata statements for 4 real data queries (8.25x); the full historical sample across all sessions: 260 metadata for 40 real (6.5x). Used 8x (the higher, more conservative figure) for margin: 5 × 8 = 40. These metadata calls are also near-instant (confirmed live, average 8.4ms, max 26ms) -- they don't meaningfully consume execution-time budget, only query *count*. |
| `max_threads` | 4 | **Derived from hard facts**: prod's 16 cores/node ÷ Trino's existing 5-concurrent-query cap for ARTE ≈ 3.2, rounded up to 4. 5 × 4 = 20 requested threads vs. 16 physical cores is far more reasonable than ClickHouse's default `auto()` thread count, which would allow 5 × 16 = 80-thread oversubscription from ARTE alone. |
| `max_bytes_to_read` | 25 GB | **Judgment call, informed by the measured baseline**: the 50M-row synthetic test read 30.15 GiB before the memory cap killed it at 17s. A byte-read cap stops a similarly-shaped but less memory-hungry query earlier on I/O alone, while leaving ~2x headroom over the 12.06 GiB a legitimate heavy (20M-row) query actually read in the same test. |
| `max_execution_time` | 60s | **Judgment call, informed by the measured baseline**: ~3.5x margin over the 16.8s cost of the 20M-row test query, while staying far under Trino's own 10–15 minute ceiling. Not a hard-derived number -- a deliberate cutoff with room for legitimately larger analytical queries. |
| Quota `MAX QUERIES` | 1600 / hour | **Measured, not just a judgment call**: originally 200/hour (generous relative to Trino's own `maxQueued=50` burst capacity, sized for normal BI-tool polling), rescaled by the same ~8x measured ClickHouse-statements-per-Trino-query multiplier described above for `max_concurrent_queries_for_user` -- this quota counts every individual ClickHouse statement including JDBC metadata overhead, so leaving it at 200 would throttle normal usage almost entirely via implementation-detail lookups, not real query volume. |
| Quota `EXECUTION TIME` | 1200s / hour | **Judgment call**: paired with the 60s per-query cap and the 1-hour interval precedent above; allows roughly 20 maximally-long queries per hour, well above realistic usage. |
