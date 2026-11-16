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
- Steady-state resident memory ~13 GiB, confirmed live via `docker stats`
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
| `max_memory_usage` | 2 GB | **Precedent**: identical to Trino's existing `query.max-memory-per-node`. Per-query; enforced for any connection, Trino or direct. See "Known scaling limit" below for how this combines with `max_memory_usage_for_user` against the node's actual available headroom and Trino's own per-partner concurrency. |
| `max_memory_usage_for_user` | 5 GB | **Judgment call, sized against live prod headroom**: a per-user *aggregate* ceiling on top of the per-query cap above, needed because a partner connecting to ClickHouse directly (bypassing Trino) isn't bound by Trino's own per-partner concurrency limit, so without this, nothing stops e.g. 20 parallel direct connections from using up memory far beyond any single query's cap. Confirmed live this is a genuine per-user *aggregate* (ClickHouse's own error is "User memory limit exceeded", distinct from and independent of the per-query `max_memory_usage` error) -- so it isn't widened by the `max_concurrent_queries_for_user` figure below, which only bounds query *count*, not summed memory. See "Known scaling limit" below for the full headroom math, the per-partner-count margin, and the trade-off against Trino's own per-partner query concurrency in prod. |
| `max_concurrent_queries_for_user` | 40 | **Measured, not just precedent-derived**: Trino's own `hardConcurrencyLimit: 5` for ARTE multiplied by a real measured factor, not assumed 1:1. Inspected dev's `system.query_log` for actual traffic from Trino's ClickHouse JDBC connector (the real `clickhouse_partners` catalog, confirmed via `http_user_agent` containing `ClickHouse-JdbcDriver`) and found every single logical Trino-level query against this catalog issues ~6-8 ClickHouse statements, not 1 -- JDBC metadata-discovery calls (`currentUser()`, table/column listing) bracketing the actual data query. One representative burst: 33 metadata statements for 4 real data queries (8.25x); the full historical sample across all sessions: 260 metadata for 40 real (6.5x). Used 8x (the higher, more conservative figure) for margin: 5 × 8 = 40. These metadata calls are also near-instant (confirmed live, average 8.4ms, max 26ms) -- they don't meaningfully consume execution-time budget, only query *count*. |
| `max_threads` | 4 | **Derived from hard facts**: prod's 16 cores/node ÷ Trino's existing 5-concurrent-query cap for ARTE ≈ 3.2, rounded up to 4. 5 × 4 = 20 requested threads vs. 16 physical cores is far more reasonable than ClickHouse's default `auto()` thread count, which would allow 5 × 16 = 80-thread oversubscription from ARTE alone. |
| `max_bytes_to_read` | 25 GB | **Judgment call, informed by the measured baseline**: the 50M-row synthetic test read 30.15 GiB before the memory cap killed it at 17s. A byte-read cap stops a similarly-shaped but less memory-hungry query earlier on I/O alone, while leaving ~2x headroom over the 12.06 GiB a legitimate heavy (20M-row) query actually read in the same test. |
| `max_execution_time` | 60s | **Judgment call, informed by the measured baseline**: ~3.5x margin over the 16.8s cost of the 20M-row test query, while staying far under Trino's own 10–15 minute ceiling. Not a hard-derived number -- a deliberate cutoff with room for legitimately larger analytical queries. |
| Quota `MAX QUERIES` | 1600 / hour | **Measured, not just a judgment call**: originally 200/hour (generous relative to Trino's own `maxQueued=50` burst capacity, sized for normal BI-tool polling), rescaled by the same ~8x measured ClickHouse-statements-per-Trino-query multiplier described above for `max_concurrent_queries_for_user` -- this quota counts every table-reading statement, including JDBC metadata lookups against `system.*` (statements with no table access, e.g. `SELECT 1`/`currentUser()`, aren't counted against it, confirmed live on the native client), so leaving it at 200 would throttle normal usage almost entirely via implementation-detail lookups, not real query volume. |
| Quota `EXECUTION TIME` | 1200s / hour | **Judgment call**: paired with the 60s per-query cap and the 1-hour interval precedent above; allows roughly 20 maximally-long queries per hour, well above realistic usage. |

## Multi-partner isolation (added onboarding INA, the 2nd partner)

All the analysis above was done with exactly one partner (ARTE) in mind. Onboarding a 2nd
partner (INA) surfaced one real gap and one non-issue, both worth recording for future
partners too.

**Gap found and fixed: the quota was a single shared counter across all partners.**
`CREATE QUOTA` with no `KEYED BY` defaults to `QuotaKeyType::NONE` (confirmed in ClickHouse's
own source, `src/Access/Quota.h` + `src/Access/QuotaCache.cpp`), which resolves to the same
empty key for every request regardless of which user issued it. Since `partner_quota` is
`TO org_role_arte, org_role_ina`, this meant ARTE and INA's hourly `MAX QUERIES`/`EXECUTION
TIME` usage was being tracked as one combined total, not two independent ones -- latent and
invisible with a single partner, but a real cross-partner interference risk with two: one
partner exhausting the shared budget would silently throttle the other, with no per-partner
visibility into why. Fixed by adding `KEYED BY user_name` to the `ALTER QUOTA` statement in
`templates/partner_resource_limits.sql.j2`, bucketing usage by the actual connecting
ClickHouse user (`org_user_<partner>`) instead. Confirmed via ClickHouse's own `ALTER QUOTA`
docs that `KEYED BY` is a normal alterable clause (not CREATE-only), so this fits the existing
`ALTER`-never-`DROP`+`CREATE` approach without any new caveats -- re-applying the same key type
on every run is a no-op.

**Non-issue, but worth confirming explicitly: the settings profile was already per-partner.**
Unlike the quota, `max_memory_usage_for_user`/`max_concurrent_queries_for_user` are enforced by
ClickHouse per actual connecting user regardless of how a `SETTINGS PROFILE` was granted (no
`KEYED BY`-equivalent exists for profiles because none is needed) -- confirmed by ClickHouse's
own distinct "User memory limit exceeded" error already being scoped to the one user, not every
role member combined. So these settings-profile figures were already correctly isolated per
partner regardless of their specific value; no profile change was needed to onboard INA.

### Known scaling limit: `max_memory_usage_for_user` headroom across partners

Sizing this value requires comparing partners' combined worst-case memory against the node's
*actual* available headroom -- not just its raw `max_server_memory_usage`, but that figure minus
the node's own steady-state baseline load (the core LMS/CMS/ingest traffic this governance
exists to protect in the first place; see "Hard facts" above for the live baseline measurement).

Confirmed live against `clickhouse02-prd`:

- `max_server_memory_usage`: 30,276,255,744 bytes = **28.2 GiB**.
- `max_memory_usage_for_user=5GB` is **4.66 GiB** in binary units (decimal GB vs. GiB -- worth
  noting since every other figure in this doc is GiB).

With 2 partners (ARTE + INA) **both genuinely isolated** (each independently reaching its own
ceiling, rather than sharing one quota-throttled pool -- see "Multi-partner isolation" above),
the combined worst case is:

| Partners simultaneously at ceiling | Combined partner memory | Total (+ 13 GiB baseline) | Margin to 28.2 GiB |
| --- | --- | --- | --- |
| 1 | 4.66 GiB | 17.66 GiB | 10.54 GiB |
| 2 (current: ARTE + INA) | 9.31 GiB | 22.31 GiB | 5.88 GiB |
| 3 | 13.97 GiB | 26.97 GiB | **1.23 GiB** |
| 4 | 18.63 GiB | 31.63 GiB | **-3.43 GiB (over)** |

This is a **judgment call, not yet a hard limit**: 5GB gives a comfortable margin at today's 2
partners, but the margin is already thin at 3 and the value fails outright at 4 -- **revisit
this value again before onboarding a 3rd partner**, not a 4th, since 3 is already close to the
edge rather than safely ahead of it. Options at that point: lower this value further (fewer GB
per partner), add a node-wide admission-control mechanism instead of static per-user caps, or
scale the ClickHouse node(s) themselves.

**Trade-off: 5 GB is below what a partner's own concurrent Trino queries can legitimately use.**
Prod Trino gives each partner a `hardConcurrencyLimit` of 3 concurrent queries (see the
`nau-analytics-kubernetes-manifests` PRs that onboarded INA for the exact
`resource-groups.json` values). Three queries each at the 2 GiB `max_memory_usage` per-query cap
sum to 5.59 GiB, above the 4.66 GiB `max_memory_usage_for_user` ceiling -- so a partner running
several concurrent heavy queries through Trino itself (not just a direct ClickHouse connection)
can now hit `User memory limit exceeded`, a behaviour that wasn't reachable under the previous,
larger per-user ceiling. This cap is a true per-user *aggregate*, not a simple sum of peak usage:
concurrent queries whose actual memory usage sums past the cap will have one fail, while
concurrent queries whose individual peaks don't coincide in time may pass even if their
individual caps summed would exceed it -- so in practice this mostly affects a partner issuing
several genuinely large queries at the same time, not routine concurrent usage. This is a
deliberate trade-off: keeping 2-3 partners within the node's real memory budget takes priority
over letting a single partner run many simultaneous large queries. If a partner's workload needs
more concurrent-heavy-query headroom than this allows, the options are the same as above --
raise this value (at the cost of thinner cross-partner margin) or reduce how many partners
share the node.

### Trino-side concurrency isolation uses nested resource groups, not a ClickHouse-level change

Trino enforces a query's resource-group
hierarchy inclusively -- a query in a child subgroup is bounded by both its own limits and
every ancestor's (per Trino's own resource-groups docs). Converting the existing flat
`partners` subgroup into a parent with per-partner child subgroups (`partners.arte`,
`partners.ina`), each with a smaller individual `hardConcurrencyLimit` than the parent's
existing total, gives each partner a guaranteed fair minimum (via `schedulingPolicy: fair`)
while leaving the parent's previously-validated combined ceiling completely unchanged -- no
re-analysis of Trino-level total resource exposure was needed for this. See the
`nau-analytics-kubernetes-manifests` PRs that onboarded INA for the actual
`resource-groups.json` values used per environment.
