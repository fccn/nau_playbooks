# clickhouse_partner_access

Provisions native, read-only, org-scoped ClickHouse access for external
data partners (e.g. ARTE), per
[fccn/nau-technical#981](https://github.com/fccn/nau-technical/issues/981)
"Option A".

For each partner in `clickhouse_partners`, this creates:
- A dedicated user (`org_user_<name>`) and role (`org_role_<name>`).
- A `ROW POLICY` scoping every table in
  `clickhouse_partner_access_org_scoped_tables` to `org = '<partner org>'`.
- A `SQL SECURITY DEFINER` view (`reporting.<name>_user_profile`) exposing
  a subset of `event_sink.user_profile` — the one table ARTE needs that has
  no native `org` column. The role only ever gets `SELECT` on this view,
  never on `event_sink.user_profile`/`event_sink.external_id` directly (see
  the template's comments for why a direct grant would silently bypass the
  org-scoping).

This is deliberately **not** wired into `deploy.yml`'s normal
`clickhouse_deploy` flow — it manages partner accounts on an existing
cluster, not the ClickHouse service itself, and is expected to be run far
less often (once per new partner, or when a partner's table/column list
changes).

## Required variables

- `clickhouse_partners`: the partner list. See
  [`defaults/main.yml`](defaults/main.yml) for the expected shape and an
  example. **The real list (with real passwords) belongs in
  `secure-nau-data`'s group_vars, never in this repo.**
- `clickhouse_user` / `clickhouse_password`: the existing admin account
  used to connect and run the provisioning SQL (already required by
  `clickhouse_docker_deploy`).
- `clickhouse_docker_container_name`: same as `clickhouse_docker_deploy`
  (defaults to `clickhouse`).

## Deploy

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini clickhouse_partner_access.yml
```

Safe to re-run: every statement is `IF NOT EXISTS`/`OR REPLACE`, so adding
a new table to `clickhouse_partner_access_org_scoped_tables` or a new
partner to `clickhouse_partners` and re-running only adds what's missing —
it won't drop or recreate existing users, roles, or passwords.

Only needs to target one cluster node (the role uses `run_once`) — every
DDL statement uses `ON CLUSTER '{{ clickhouse_partner_access_cluster }}'`,
so ClickHouse's own distributed-DDL queue (backed by Keeper) fans it out to
every replica automatically.

## Adding a new partner

Add an entry to `clickhouse_partners` (in `secure-nau-data`, per
environment):

```yaml
clickhouse_partners:
  - name: arte
    org: "AMA"
    password: "{{ clickhouse_partner_arte_password }}"
```

`name` becomes the suffix for every object this role creates
(`org_user_arte`, `org_role_arte`, `reporting.arte_user_profile`). No code
change is needed in this role itself — the table/column lists in
`defaults/main.yml` are shared across all partners.

## Troubleshooting

If you ever need to run this SQL manually (e.g. to debug a failed run) with
a standalone `clickhouse-client`/Docker image rather than
`docker exec`-ing into the actual ClickHouse container, make sure the
client version matches the server version. The `clickhouse/clickhouse-client:latest`
Docker Hub tag is a stale, much older client build (confirmed: `latest`
resolved to client `22.1.3.7` against a `25.3.6.56` server) — its parser
doesn't recognise the `DEFINER`/`SQL SECURITY` grammar used in the view
below and fails with a generic `Syntax error ... Expected one of: token,
Dot, UUID, ON, TO INNER UUID, TO, OpeningRoundBracket, AS` pointing at
`DEFINER`, which looks like a real syntax problem but isn't. Use
`clickhouse/clickhouse-server:<exact-version>` instead (it ships the
matching `clickhouse-client` binary via `--entrypoint clickhouse client`),
or — simplest — just exec into the real container, which is what this
role's tasks do (`docker exec ... clickhouse-client ...`) and therefore
never hits this.

Also note: `GRANT` only accepts **one** `db.table` target per statement
(unlike `ROW POLICY`, which does accept a comma-separated table list under
one policy name) — this is why `partner_access.sql.j2` loops to emit one
`GRANT SELECT ON <table> ...` per table in
`clickhouse_partner_access_org_scoped_tables`, rather than a single
comma-joined `GRANT`.

## Removing a partner

Not automated (on purpose — this role only ever grants, never revokes, to
avoid an accidental variable-list edit silently dropping access). To
offboard a partner, drop their user/role/view manually via
`clickhouse-client`:

```sql
DROP USER IF EXISTS org_user_<name> ON CLUSTER '<cluster>';
DROP ROLE IF EXISTS org_role_<name> ON CLUSTER '<cluster>';
DROP ROW POLICY IF EXISTS org_filter_<name> ON <tables...> ON CLUSTER '<cluster>';
DROP VIEW IF EXISTS reporting.<name>_user_profile ON CLUSTER '<cluster>';
```
