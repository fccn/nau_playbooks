# clickhouse_partner_access

Provisions native, read-only, org-scoped ClickHouse access for external
data partners (e.g. ARTE), per
[fccn/nau-technical#981](https://github.com/fccn/nau-technical/issues/981)
"Option A".

For each partner in `clickhouse_partners`, this creates:
- A dedicated user (`org_user_<name>`) and role (`org_role_<name>`).
- A `ROW POLICY` scoping every table in
  `clickhouse_partner_access_org_scoped_tables` to
  `org IN ('<partner org 1>', '<partner org 2>', ...)` -- a partner's
  courses can span more than one platform `org` namespace (e.g. ARTE:
  both `AMA` and `portugaldigital`), so `orgs` is a list, not a single
  string.
- A `SQL SECURITY DEFINER` view (`reporting.<name>_user_profile`) exposing
  a subset of `event_sink.user_profile` (the one table with no native
  `org` column), plus the `actor_id` looked up along the way via
  `event_sink.external_id` -- the role only ever gets `SELECT` on the
  view, never on `event_sink.user_profile`/`event_sink.external_id`
  directly.

It also maintains a resource-governance `SETTINGS PROFILE` + `QUOTA`
shared by every `org_role_<name>` -- see
[Resource governance](#resource-governance-profile--quota) below.

Runs as part of `deploy.yml`'s ClickHouse play, restricted to a single
node (ClickHouse's own distributed-DDL queue fans `ON CLUSTER` DDL out to
the rest of the cluster).

## Required variables

- `clickhouse_partner_access_enabled`: kill switch, defaults to `false`.
  Must be explicitly set `true` in an environment's own group_vars
  (alongside `clickhouse_partners`) before anything is provisioned there.
- `clickhouse_partners`: the partner list. See
  [`defaults/main.yml`](defaults/main.yml) for the shape. **Real values
  belong in `secure-nau-data`'s group_vars, never in this repo.**
- `clickhouse_user` / `clickhouse_password` / `clickhouse_docker_container_name`:
  same as `clickhouse_docker_deploy`.

## Deploy

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml \
  --limit clickhouse_servers --tags clickhouse_partner_access
```

## Enabling per environment

Both `clickhouse_partner_access_enabled: false` and `clickhouse_partners: []`
default to a no-op, so merging this role (or a `secure-nau-data` PR with
real partner entries) never provisions anything by itself. Rollout to an
environment is a separate, reviewable change: flip
`clickhouse_partner_access_enabled: true` in that environment's group_vars.

Safe to re-run -- almost every per-partner statement is `IF NOT EXISTS`,
so adding a table or partner and re-running only adds what's missing.
A few exceptions, all needed so a config change actually takes effect
on an already-provisioned environment (see [Why some org-scoped tables
still need a DEFINER
view](#why-some-org-scoped-tables-still-need-a-definer-view)):
- The Category 1 row policy gets an `ALTER ROW POLICY` right after its
  `CREATE ... IF NOT EXISTS` -- `CREATE ... IF NOT EXISTS` alone never
  updates an already-existing policy's org list, so without the
  `ALTER`, a partner's `orgs` list change (e.g. onboarding a second
  org) would silently never apply on a re-run.
- `reporting.<partner>_user_profile` and `reporting.<partner>_problem_attempts`
  are both `CREATE OR REPLACE`, so a changed column list actually takes
  effect. The latter is preceded by an idempotent cleanup
  (`REVOKE`/`DROP ROW POLICY IF EXISTS`) for environments that ran an
  older version of this role against `reporting.int_problem_results`
  directly.
- The user's own password gets the same treatment: `CREATE USER IF NOT
  EXISTS ... IDENTIFIED WITH sha256_hash BY ...` only sets it on first
  creation, so a rotated `partner.password` in `secure-nau-data` would
  otherwise never take effect on a re-run. An `ALTER USER IF EXISTS`
  right after re-asserts it from the (possibly updated)
  `clickhouse_partners` list on every run. `sha256_hash` (not
  `sha256_password`) is used so the plaintext password is never part of
  the DDL statement itself -- with `clickhouse_partner_access_on_cluster:
  true`, that statement is what ends up persisted in Keeper's
  distributed-DDL queue/changelog, which has no authentication of its own.

The shared resource-governance profile/quota (see below) are rebuilt
from the full `clickhouse_partners` list on every run (via `ALTER`, not
a destructive drop), so an existing partner's limits/quota attachment
also stay in sync with the current defaults on every deploy -- see
[Resource governance](#resource-governance-profile--quota).

## Adding a new partner

Add an entry to `clickhouse_partners` (in `secure-nau-data`, per environment):

```yaml
clickhouse_partners:
  - name: arte
    orgs: ["AMA", "portugaldigital"]
    password: "{{ clickhouse_partner_arte_password }}"
```

`orgs` is always a list, even for a partner with a single platform org --
it's rendered into `org IN (...)` either way.

`name` becomes the suffix for every object this role creates
(`org_user_arte`, `org_role_arte`, `reporting.arte_user_profile`,
`reporting.arte_problem_attempts`). No code change needed -- the
table/column lists in `defaults/main.yml` are shared across all
partners. `name` must also be unique across `clickhouse_partners` --
the role asserts this, since a duplicate would silently shadow the
earlier entry (its password and orgs are what end up applied).

`password` must be at least `clickhouse_partner_access_min_password_length`
characters (16 by default) -- the role asserts this too, since `ALTER
USER` re-applies it on every run, and a blank/null/too-short value would
otherwise overwrite the live credential instead of failing validation
first. Avoid `{{`, `{%` or `{#` in a generated password: a value
containing one would fail Jinja templating partway through this role
(fails closed, live credential untouched) but briefly echo the vars
file to the terminal/`ansible.log` while doing so. Mark such a value
`!unsafe` in `secure-nau-data` if ever needed.

A partner's password lives in two repos, not just `secure-nau-data`:
Trino's own copy, used for the `clickhouse_partners` catalog connection
(`TRINO_CLICKHOUSE_PARTNERS_ARTE_PASSWORD` in
[nau-analytics-kubernetes-manifests](https://github.com/fccn/nau-analytics-kubernetes-manifests/pull/164)),
has to be rotated at the same time -- rotating only this role's copy
breaks the partner's Trino queries until Trino's secret is updated and
its pods restart.

## Why some org-scoped tables still need a DEFINER view

Most tables get a plain `ROW POLICY` + `GRANT SELECT` (Category 1): native
`org` column, no PII. Two need a `SECURITY DEFINER` view instead
(`reporting.<partner>_user_profile`, `reporting.<partner>_problem_attempts`),
running under `clickhouse_partner_access_view_definer`'s privileges so
`org_role_<partner>` only needs `SELECT` on the wrapper:

- `event_sink.user_profile` has no `org` column at all.
- `reporting.int_problem_results` has an `org` column, but it's a view
  that joins `reporting.dim_course_blocks` (itself backed by two
  Dictionaries with no `org` column) for display-name metadata.
  ClickHouse checks a plain view's grants against the querying user's
  own privileges down the whole chain, so a direct grant fails, and
  granting the chain itself would expose every course's/block's name
  platform-wide.

See `templates/partner_access.sql.j2`.

## Resource governance (profile + quota)

Independently of the per-partner org-scoping above, every `org_role_<name>`
is attached to one shared `SETTINGS PROFILE`
(`clickhouse_partner_access_settings_profile`, default `partner_readonly`)
and one shared `QUOTA` (`clickhouse_partner_access_quota_name`, default
`partner_quota`), bounding worst-case per-query cost and per-hour query
volume so partner access can't impact core LMS/CMS ClickHouse load. See
[docs/resource_governance_analysis.md](docs/resource_governance_analysis.md)
for the full scalability/performance-impact analysis (prod hardware facts,
existing Trino precedents, and a live synthetic load test in dev) behind
these specific values -- done as part of
[fccn/nau-technical#981](https://github.com/fccn/nau-technical/issues/981):

| Setting | Default | Rationale |
| --- | --- | --- |
| `max_memory_usage` | 2 GB | Matches Trino's existing `query.max-memory-per-node` cap for the same partner access. Per-query; applies regardless of whether the session reached ClickHouse via Trino or a direct connection. |
| `max_memory_usage_for_user` | 10 GB | Per-user *aggregate* ceiling (confirmed live, not just per-query) on top of the per-query cap above (5 × `max_memory_usage`, reusing Trino's own 5-concurrent-query cap for ARTE): without this, a partner connecting to ClickHouse directly (bypassing Trino, and so Trino's own concurrency cap) could still use up to `max_memory_usage` per query across many parallel connections. Being a true aggregate (not per-query) is what makes it safe for `max_concurrent_queries_for_user` below to be much higher than Trino's raw concurrency figure. |
| `max_concurrent_queries_for_user` | 40 | 5 (Trino's concurrency cap for ARTE) × ~8, a multiplier measured from real dev traffic, not assumed: a single Trino-level query against the ClickHouse partner catalog issues ~6-8 ClickHouse statements (JDBC metadata lookups around the actual data query), confirmed via `system.query_log`. |
| `max_threads` | 4 | Prod's 16 cores per ClickHouse node, divided by Trino's existing 5-concurrent-query cap for ARTE. |
| `max_bytes_to_read` | 25 GB | Stops an outsized scan on bytes read (not just memory/time) with headroom above a legitimate heavy query's measured read volume in the synthetic load test. |
| `max_execution_time` | 60s | ~3.5x margin over the measured cost of a deliberately heavy query in a synthetic load test, far under Trino's own 10-15 min ceiling. |
| quota `MAX QUERIES` | 1600 / hour | Same ~8x measured multiplier as `max_concurrent_queries_for_user` applied to an original 200/hour target (itself generous relative to Trino's own partner burst-queue capacity) -- this quota counts every ClickHouse statement, including JDBC metadata overhead, not just logical queries. |
| quota `EXECUTION TIME` | 1200s / hour | Paired with the 60s per-query cap and the quota's 1-hour interval; allows roughly 20 maximally-long queries per hour. |

Rendered once per run (`templates/partner_resource_limits.sql.j2`), not
per-partner: `CREATE SETTINGS PROFILE/QUOTA IF NOT EXISTS` followed by
`ALTER ... SETTINGS ... TO <full list>`, **never `DROP` + `CREATE`**.
ClickHouse's `TO`/`SETTINGS` clauses on `ALTER SETTINGS PROFILE`/`QUOTA`
are a full replace, not additive (confirmed live against ClickHouse 25.3),
so `ALTER` reaches the exact same end state as `DROP` + `CREATE` as long as
the template always supplies the complete `clickhouse_partners` list --
which it does. `ALTER` is deliberately preferred over `DROP` + `CREATE`,
for two reasons confirmed live:
- **Fails closed instead of open.** A mid-run failure between `DROP` and
  `CREATE` would leave `org_role_*` with zero enforcement until the next
  successful run -- exactly when a deploy issue makes that most likely.
  `ALTER` never passes through a state where the object doesn't exist, so
  a failure here can only leave the *previous* values in place, never none
  at all.
- **Preserves the quota's usage counters.** `DROP` + `CREATE` silently
  resets `system.quotas_usage` on every run, not just once per real
  interval boundary; `ALTER` doesn't.

One exception to "full replace, not additive", confirmed live: `ALTER
QUOTA ... FOR INTERVAL <N> ...` only replaces an existing interval of the
*same* length. If `clickhouse_partner_access_quota_interval_hours` itself
changes between runs, the previous interval is left in place *alongside*
the new one (both independently enforced) rather than replaced --
`system.quotas.durations` is the column that would show e.g. `[3600,
7200]` instead of just `[7200]`. (`ALTER SETTINGS PROFILE ... SETTINGS`
doesn't have this problem -- confirmed live it's a genuine full replace,
including removing a setting entirely from `system.settings_profile_elements`
when it's omitted from a later `ALTER`, not just leaving it
unconstrained.) A task before rendering the template queries
`system.quotas.durations`. The template first applies the current
interval via `ALTER QUOTA`, then emits `ALTER QUOTA ... FOR INTERVAL
<stale> SECOND NO LIMITS ...` for any duration that doesn't match the
current setting -- apply first, clear second, so a mid-run failure on the
cleanup step leaves the old/both intervals enforced, never none -- 
confirmed live this leaves exactly one interval (the current one) behind,
not two.

Rebuilding the `TO` list from the full `clickhouse_partners` list every
run still means:
- Already-existing partners automatically pick up any changed limit values
  on the next deploy -- no need to touch/recreate their `CREATE USER`.
- Removing a partner from `clickhouse_partners` and re-running
  automatically drops them from the profile/quota's `TO` list (unlike the
  per-partner grants/views below, which are never auto-revoked). **This
  is not a revocation** -- see [Removing a partner](#removing-a-partner):
  a removed partner can still log in and read their org's data under the
  user-level `readonly` profile alone, with no memory/time/byte caps or
  quota, until their user/role/grants are dropped too.

Must run after the per-partner loop above, since it references every
`org_role_<name>` in its `TO` clause -- all of those roles must already
exist. A task after applying this template also queries the profile's and
the quota's `apply_to_list` (`system.settings_profiles`/`system.quotas`)
separately and asserts every partner's role is an exact member of each,
so a `CREATE`/`ALTER` that silently didn't cover a partner on one of the
two objects (rather than erroring outright) still fails the deploy
loudly instead of leaving that partner partially unconstrained.

## Troubleshooting

- `clickhouse/clickhouse-client:latest` on Docker Hub is a stale build
  (resolved to `22.1.3.7` against our `25.3.6.56` server) that can't
  parse the `DEFINER`/`SQL SECURITY` grammar used here, and fails with a
  misleading syntax error. Use `clickhouse/clickhouse-server:<version>`
  instead, or just exec into the real container (what this role does).
- `GRANT` only accepts one `db.table` per statement (unlike `ROW POLICY`,
  which accepts a list) -- that's why the template loops to emit one
  `GRANT` per table.

## Removing a partner

**Removing a partner from `clickhouse_partners` and re-running is not a
revocation** -- it only drops the partner from the shared profile/quota's
`TO` list (see [Resource governance](#resource-governance-profile--quota)).
Nothing else is automated: the partner's user/role/row-policy/view grants
stay in place, so between that re-run and the manual drop below, the
partner can still log in and read their org's data -- just with weaker
governance (only the user-level `readonly` profile, no caps or quota)
instead of none at all. To actually revoke access, do both in the same
change window -- drop the objects below first (or at least don't treat
the `clickhouse_partners` edit alone as "done" if the goal is to cut the
partner off, not just loosen their limits):

```sql
DROP USER IF EXISTS org_user_<name> ON CLUSTER '<cluster>';
DROP ROLE IF EXISTS org_role_<name> ON CLUSTER '<cluster>';
DROP ROW POLICY IF EXISTS org_filter_<name> ON <tables...> ON CLUSTER '<cluster>';
DROP VIEW IF EXISTS reporting.<name>_user_profile ON CLUSTER '<cluster>';
DROP VIEW IF EXISTS reporting.<name>_problem_attempts ON CLUSTER '<cluster>';
```
