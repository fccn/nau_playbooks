# Percona XtraDB docker deploy role

This ansible role deploys an Percona XtraDB instance using a docker-compose.yml file.
This role can be deployed to multiple hosts creating an Percona XtraDB cluster.

## Required Variable

You have to configure this variable:
- `xtradb_mysql_root_password`

## Engine settings

The engine settings of [nau-technical#1100](https://github.com/fccn/nau-technical/issues/1100) are all **optional**: a
variable that is not defined is not written to `custom.cnf`, so the role renders the same file as before until an
environment opts in. See `defaults/main.yml` for the units, the limits and the cost of each one.

| Variable | What it does | Needs |
|----------|--------------|-------|
| `xtradb_docker_slow_query_log` | Slow query log in `/data/xtradb/slow.log.NNNNNN`, rotated by mysqld (`..._max_size` x `..._max_files` is the most it uses). Threshold `..._long_query_time` (1 s). | Restart, or `SET GLOBAL` (see `defaults/main.yml`) |
| `xtradb_docker_innodb_redo_log_capacity` | Redo log size, 8M to 99G (MySQL default 100M). Absorbs write bursts. Allocated in full in `/data`. | Restart, or `SET GLOBAL` |
| `xtradb_docker_skip_name_resolve` | No DNS lookup per new connection (3 DNS queries per connection in a local test, the image keeps the host cache off). | Restart, and the account check below |
| `xtradb_docker_gcache_size` | Galera write-set cache (128M default): how long a node can be away and rejoin by IST. Allocated in full in `/data`. | Restart |

The deploy fails before touching a node if a size has no `M` / `G` unit (a bare number is in bytes), is out of range, or
if the slow log threshold is `0`.

Set them in the inventory of the environment (`secure-nau-data`), one environment at a time. Do **not** use `SET PERSIST`:
it writes `mysqld-auto.cnf` in the data directory, which wins over `custom.cnf` at every restart and is not in this
repository. Use `SET GLOBAL` for an immediate effect and set the same value in the inventory.

### Measure first

```bash
make --no-print-directory -C /nau/ops/xtradb/ xtradb-innodb-pressure INTERVAL=30
```

Read-only (it only reads `performance_schema`). Run it on each node a few times in the busiest hour, before and after a
change. It prints the redo written per second and how full the redo is, the dirty pages, the row lock waits, the new
connections per second (and whether they do DNS lookups), the slow queries, and how many minutes of write-sets the Galera
cache holds at the current rate.

A checkpoint age that goes over about 75 % of the redo capacity in a burst means the writers are close to waiting: in a
local test with the default 100M, a burst that took it to 83 % made them stall, and at 4 % of a 2G capacity it did not.
The "IST window" is an estimate from the bytes written and the cache size; the line below it, from the write-sets in the
cache now, is the real one.

### Before `xtradb_docker_skip_name_resolve`

An account whose host is a host name stops matching, and for a wildcard host name (`app@%.example.com`) there is no
warning in the log. On every node:

```sql
SELECT user, host FROM mysql.user WHERE host REGEXP '[A-Za-z]' AND host <> 'localhost';
```

Enable it only if this returns nothing (an IPv6 address such as `::1` is listed too, ignore those). The `root@%` account
that the `make` health checks and the backup use over `127.0.0.1` has to exist: check it with
`SELECT user, host FROM mysql.user WHERE user = 'root';`.

### Before enlarging `xtradb_docker_gcache_size`

Check the kernel and the file system of the nodes. Percona PXC-5340 (open) reports write amplification on the memory
mapped cache with the large folio support of recent kernels (XFS since 5.18, ext4 since 6.16). Compare the disk writes
of the node before and after on one node first.

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
