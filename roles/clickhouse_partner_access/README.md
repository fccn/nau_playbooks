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
  a subset of `event_sink.user_profile` (the one table with no native
  `org` column) -- the role only ever gets `SELECT` on the view, never on
  `event_sink.user_profile`/`event_sink.external_id` directly.

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

Safe to re-run -- every statement is `IF NOT EXISTS`/`OR REPLACE`, so
adding a table or partner and re-running only adds what's missing.

## Adding a new partner

Add an entry to `clickhouse_partners` (in `secure-nau-data`, per environment):

```yaml
clickhouse_partners:
  - name: arte
    org: "AMA"
    password: "{{ clickhouse_partner_arte_password }}"
```

`name` becomes the suffix for every object this role creates
(`org_user_arte`, `org_role_arte`, `reporting.arte_user_profile`). No
code change needed -- the table/column lists in `defaults/main.yml` are
shared across all partners.

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

Not automated (this role only ever grants, never revokes). Drop manually:

```sql
DROP USER IF EXISTS org_user_<name> ON CLUSTER '<cluster>';
DROP ROLE IF EXISTS org_role_<name> ON CLUSTER '<cluster>';
DROP ROW POLICY IF EXISTS org_filter_<name> ON <tables...> ON CLUSTER '<cluster>';
DROP VIEW IF EXISTS reporting.<name>_user_profile ON CLUSTER '<cluster>';
```
