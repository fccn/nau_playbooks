# XtraDB Prometheus exporter docker deploy

Deploys the [`mysqld_exporter`](https://github.com/prometheus/mysqld_exporter) next to the Percona XtraDB
container of each node, so the Prometheus/Grafana of the Kubernetes cluster can show the health of the
MySQL + Galera cluster: node state, cluster size, flow control, replication queues, connections, binary log size.

It is a separate role, called as the last task of the "Deploy to XtraDB database" play of `deploy.yml`. It never
restarts the `xtradb` container, and a failure there cannot leave the keepalived priority lowered, because the
priority is already restored by then.

```
xtradb VM
  xtradb container   :3306  <--- local queries, every scrape ---+
  mysqld-exporter    :9104  <--- Prometheus (k8s) scrapes this --+
```

## What it does, on each node, in order

1. Validates the credentials (see the required variable below).
2. Waits for the node to be a synced Galera member (`wsrep_ready` and `wsrep_local_state` = 4). If it is not, the
   role fails **before** touching the MySQL user.
3. Creates the MySQL user of the exporter, only when it is missing, has another password or has other privileges.
   Galera replicates it, so the first node creates it and the next ones find it ready and skip this step.
4. Writes the `Makefile` and `/nau/ops/xtradb-exporter/.my.cnf` (the folder keeps the `xtradb-` name, the container does not, see Notes) (owner `65534`, mode `0400`) and starts the exporter container.
5. Waits until `http://<node>:9104/metrics` answers with `mysql_up 1`.

The MySQL user has only `PROCESS`, `REPLICATION CLIENT` and `SELECT`, and at most 3 connections.
Anything else it finds on the user is removed (global, schema, table or column privileges, dynamic privileges, grant
option), and the user is only touched when it differs. Roles granted to the user are not checked.
The folder is `0755` so that snmpd can run the healthcheck; the credentials file inside is readable only by the container user.

## Required variable

Define it per environment in `secure-nau-data` (`envs/<env>/group_vars/xtradb_servers.yml`):

```yaml
xtradb_exporter_mysql_password: <exactly 32 letters and digits>
```

- Letters and digits only. The exporter builds its connection string from the password, and a `?` in it makes
  MySQL read part of the options as the database name (`Unknown database '&lock_wait_timeout=2'`).
- One password per environment, because the user is one per cluster. Keep a copy in the NAU password database.
- The role fails, without printing the value, if it is missing, the wrong length or has symbols. The value that
  is committed in `secure-nau-data` is a placeholder that fails on purpose.

Generate one with `openssl rand -hex 16`.

## Deploy

A full XtraDB deploy deploys the exporter too, as its last step, **when `xtradb_exporter_mysql_password` is defined**
in secure-nau-data. Without a valid one the exporter is skipped with a message and the XtraDB deploy goes on:

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit xtradb_servers -e xtradb_deploy=true
```

To deploy only the exporter, add the tag. It stays one node at a time (`serial`), and an explicit run fails on a
missing or invalid password instead of skipping. Start with the last node (the backup one):

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml \
  --limit 'xtradb_servers[-1]' -e xtradb_deploy=true --tags xtradb_exporter
```

Preview what it would change (it connects to the node, reads, and writes nothing):

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml \
  --limit 'xtradb_servers[-1]' -e xtradb_deploy=true --tags xtradb_exporter --check --diff
```

`<env>` is the folder of `secure-nau-data` (`development`, `staging`, `production`), the hosts are named `-dev`, `-qa`
and `-prd`.

The credentials file and the SQL are hidden from `--diff` and the logs (`no_log`).

Running it again does not restart the exporter, and the MySQL user is only touched when it differs. The recap still
shows `changed` for the shell tasks of `ansible-docker-deploy` (as in the other roles), so it does not tell if
something drifted. The container is recreated only when the credentials file or the compose file change, for example
on a password rotation.

If a node was set up by hand before this role existed, the first run recreates the exporter container once (the compose
file gains resource limits and `cap_drop`). The database is not touched. A container created with the earlier name
`xtradb-exporter` is replaced by `mysqld-exporter`, with no port clash.

### Check it

```bash
cd /nau/ops/xtradb-exporter && make healthcheck
```

It checks that the container is `running` (not restarting or exited) and that the exporter can query the XtraDB of
its node (`mysql_up 1`). It asks the exporter for one collector only, so it uses one MySQL connection and, together
with the scrape of Prometheus, stays under the 3 connections of the MySQL user. A full scrape uses 2.

```bash
curl -s <node ip>:9104/metrics | grep -E '^mysql_up |^mysql_global_status_wsrep_(ready|cluster_size|local_state) '
```

Expected: `mysql_up 1`, `wsrep_ready 1`, `wsrep_cluster_size 3` and `wsrep_local_state 4` (Synced).

## Monitoring with SNMP (Icinga)

When `xtradb_exporter_mysql_password` is defined, `group_vars/xtradb_servers.yml` adds an `extend` to the snmpd
configuration of the XtraDB nodes, like the other roles do. It prints `OK` when `make healthcheck` passes:

```bash
snmpwalk -v 2c -c <community> <node> 'NET-SNMP-EXTEND-MIB::nsExtendOutputFull."xtradb_exporter_healthcheck"'
```

- It reaches the node with the snmpd step of the XtraDB play, which runs with `-e xtradb_deploy=true` and no tag or with
  `--tags snmpd`. A run with only `--tags xtradb_exporter` does not touch snmpd.
- **The Icinga service that reads it has to be created in Icinga**, it is not part of this repository.
- The check is not added to `makefile_healthcheck` on purpose. That list runs on the `healthcheck`, `upgrade_and_reboot`,
  `rolling_execute` and `server_maintenance` playbooks and waits up to 25 minutes for it, so a dead metrics exporter
  would block the maintenance of the database nodes. To add it anyway, define in `group_vars/xtradb_servers.yml`
  `xtradb_exporter_makefile_healthcheck: "{{ [ xtradb_exporter_docker_deploy_base_folder ] if ( xtradb_exporter_configured | bool ) else [] }}"`
  and add it to `makefile_healthcheck` in `group_vars/all/monitoring.yml`.

## Prometheus and the firewall

This role only exposes the metrics. Prometheus must be told to scrape `<node IP>:9104` (a `ScrapeConfig` in the
`monitoring` global app of `nau-kubernetes-manifests`), and the Kubernetes worker nodes must reach port `9104` of
the XtraDB VMs.

If an environment enables `xtradb_servers_firewall_ports` in `secure-nau-data`, add port `9104` for the Kubernetes
workers there (there is a commented example), or the scrape stops without any error on the node.

The exporter has no auth or TLS, so it listens only on the VM IP (`ansible_host`) and not on `localhost`.
Set `xtradb_exporter_listen_ip: ""` to listen on all interfaces.

## Rotate the password

Change `xtradb_exporter_mysql_password` in `secure-nau-data` and deploy each node as above. The first node updates
the MySQL user, every node rewrites its file and recreates its container. Between the first node and the last one
the other nodes keep scraping with the old password and report `mysql_up 0` until their turn, so do it in one go.

## Variables

| Variable | Default | What |
|---|---|---|
| `xtradb_exporter_mysql_password` | required | 32 letters and digits |
| `xtradb_exporter_mysql_user` | `exporter` | MySQL user |
| `xtradb_exporter_docker_image` | `docker.io/prom/mysqld-exporter:v0.21.0` | pinned version |
| `xtradb_exporter_listen_ip` / `_listen_port` | VM IP / `9104` | where it listens |
| `xtradb_exporter_collector_flags` | `[--collect.binlog_size]` | extra collectors |
| `xtradb_exporter_docker_container_name` | `mysqld-exporter` | name of the exporter container |
| `xtradb_exporter_xtradb_container_name` | `xtradb` | container of the database on the node |
| `xtradb_exporter_mem_limit` / `_pids_limit` | `128m` / `64` | container limits (it uses about 8 MiB) |
| `xtradb_exporter_restart_max_retries` | `5` | restarts after a crash, never reset |
| `xtradb_exporter_uid` / `_gid` | `65534` | user of the container and owner of the credentials file |

## Notes

- **Collectors.** The exporter enables `global_status`, `global_variables`, `slave_status`, `info_schema.innodb_cmp`,
  `info_schema.innodb_cmpmem` and `info_schema.query_response_time` by default, and this role adds `binlog_size`.
  The last three only report when the server uses compressed tables or has `query_response_time` enabled.
  Do not add the `info_schema.tables`, `schema_size`, `auto_increment.columns` or `perf_schema.*` collectors to this
  scrape: they scan `information_schema`/`performance_schema` and can be heavy on a busy database.
- **No docker healthcheck on the container.** The deploy helper waits until the `docker ps` status of every
  container of the host is empty or `healthy`, so an `unhealthy` exporter would block the deploys of the other roles.
- **Restart policy: `on-failure:5`, not `always`.** With `always`, an exporter that cannot start (for example it cannot
  read its credentials file) shows as `Restarting (1)` in `docker ps` forever, and the wait above never accepts it, so
  the XtraDB deploy retries for up to 20 minutes and fails. With `on-failure:5` it gives up after 5 restarts and stays
  `Exited`, which `docker ps` does not list. Measured with the real exporter (docker 29, two daemon restarts):
  - a docker restart or a host reboot starts it again, and does not use up the 5 retries;
  - docker starts it again only if its last exit was not 0. The exporter exits 143 on SIGTERM, and the compose file sets
    `stop_signal: SIGKILL` (exit 137) so that does not depend on the exporter version. A container that exited 0 stayed
    stopped after the restart;
  - the retries are never reset: after 5 crashes it stays down until the next deploy recreates the container. The
    Prometheus alert and the SNMP healthcheck report it, and re-running the role brings it back.
  Check this again when you change `xtradb_exporter_docker_image`.
- **Container name.** It is `mysqld-exporter` and not `xtradb-...` because the memory healthcheck of the xtradb role
  (`egrep "^xtradb"` in its Makefile) matches containers by that prefix and would also check the exporter.
- **Version.** The exporter is still 0.x and minor versions change metric names and types. Read its
  [changelog](https://github.com/prometheus/mysqld_exporter/blob/main/CHANGELOG.md), try it on dev and check the
  dashboards and alerts before changing `xtradb_exporter_docker_image`.
- **Logs and metrics path.** The container uses the default docker logging driver of the host.

## Remove it

On the node:

```bash
cd /nau/ops/xtradb-exporter && docker-compose down && cd / && rm -rf /nau/ops/xtradb-exporter   # xtradb-exporter is the folder, the container is mysqld-exporter
```

When the exporter is gone from every node, drop the shared user (Galera removes it everywhere):

```bash
docker exec -i xtradb bash -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -h127.0.0.1 -e "DROP USER IF EXISTS \"exporter\"@\"127.0.0.1\";"'
```
