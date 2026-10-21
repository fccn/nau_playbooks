# Percona XtraDB docker deploy role

This ansible role deploys an Percona XtraDB instance using a docker-compose.yml file.
This role can be deployed to multiple hosts creating an Percona XtraDB cluster.

## Required Variable

You have to configure this variable:
- `xtradb_mysql_root_password`

## Certificates

Prior to deploy this role, you need to generate certificates.
This will create a `cert` folder with multiple files related to certificates.

```bash
mkdir -m 777 -p ./cert && docker run --name pxc-cert --rm -v ./cert:/cert percona/percona-xtradb-cluster:8.0 mysql_ssl_rsa_setup -d /cert
```

Then you need to configure ansible to use those files and then configure the use of this role with:

```yaml
vars:
  xtradb_certs_ca_key: /path/to/ca-key.pem
  xtradb_certs_ca: /path/to/ca.pem
  xtradb_certs_client_cert: /path/to/client-cert.pem
  xtradb_certs_client: /path/to/client-key.pem
  xtradb_certs_private_key: /path/to/private_key.pem
  xtradb_certs_public_key: /path/to/public_key.pem
  xtradb_certs_server_cert: /path/to/server-cert.pem
  xtradb_certs_server_key: /path/to/server-key.pem
```

## Cluster initialization

To create a cluster you need firstly deploy to an empty node.
Then for the next nodes you need to deploy with the variables:
-  `xtradb_cluster_initialization` with `True`.
-  `xtradb_cluster_join` with a value of the host name or IP address of the first node deployed;

Example to get the first cluster node host name or IP address:
```yaml
xtradb_cluster_join: "{{ hostvars[groups['xtradb_servers'][0]].ansible_host }}"
```

## Binary logs

The binary logs are written in the data volume (`/data/xtradb`), every node keeps a full copy, and Galera does
not read them: they are only used for point-in-time recovery between two backups. Unbounded, they fill `/data`.
See [nau-technical#1097](https://github.com/fccn/nau-technical/issues/1097).

| Variable | Default | |
|----------|---------|-|
| `xtradb_docker_binlog_expire_logs_seconds` | `604800` (7 days) | How long to keep them: at least the interval between two backups, 2 intervals tolerate one failed backup. PROD is backed up daily and sets `172800` in `secure-nau-data`. DEV and STAGE are weekly and keep the default (one interval). |
| `xtradb_docker_binlog_space_limit` | `30G` | Hard cap for the total size (Percona `binlog_space_limit`): the oldest ones are purged whatever their age. Empty removes the cap. Always give a unit: a bare number is in **bytes**. |
| `xtradb_docker_binlog_row_image` | not set | `MINIMAL` logs only the changed columns (-32 % of binlog bytes on a synthetic graded submission in a local test, not measured on production data). Test it on STAGE first, tools that read the binary logs must accept partial rows. |

The deploy fails before touching a node if the retention is `0` (it would turn the purge off) or if the cap has no
unit or is below `1G`.

Both settings only need a restart of each node, which the deploy does one node at a time. The restart also purges
the expired binary logs, so the space is reclaimed by the deploy itself.

Do not set `expire_logs_days` in `custom.cnf` or at runtime together with `binlog_expire_logs_seconds`: the server
rejects it (error 3683 / 4113) and ignores `expire_logs_days` at start-up.

### Reclaim the space before the next deploy

On each node, one at a time, with the cluster healthy. `PURGE` and the settings are **not** replicated by Galera.

```bash
make -C /nau/ops/xtradb/ xtradb-shell
```
```sql
SHOW BINARY LOGS;                                -- before
SET GLOBAL expire_logs_days = 0;                 -- first, the two settings cannot both be set
SET GLOBAL binlog_expire_logs_seconds = 172800;  -- the value of the environment
FLUSH BINARY LOGS;                               -- nothing is purged until the logs rotate
SHOW BINARY LOGS;                                -- after
```

The runtime values are lost on a restart: the deploy is what makes them permanent.

## References

- https://docs.percona.com/percona-xtradb-cluster/8.0/docker.html

## Example

Deploy first node, then join all other other nodes, then just run a normal deploy without the initialization.

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers[0]' -e xtradb_deploy=true -e xtradb_cluster_initialization=true
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers:!xtradb_servers[0]' -e xtradb_deploy=true -e serial_number=10
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers' -e xtradb_deploy=true
```

To add a new node to existing cluster add it to the `xtradb_servers` group, then deploy to it.
After that deploy and joining to existing cluster, the existing nodes should know it for on the CLUSTER_JOIN string, so we need to deploy all nodes again:
```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit new_node -e xtradb_deploy=true
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers' -e xtradb_deploy=true
```
