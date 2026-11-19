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

## References

- https://docs.percona.com/percona-xtradb-cluster/8.0/docker.html

## State transfer donor

`xtradb_docker_wsrep_sst_donor` (`wsrep_sst_donor` in `custom.cnf`) defaults to every other node of
`xtradb_docker_cluster_group` (`xtradb_servers`), the last one first:

| Node | `wsrep_sst_donor` |
|---|---|
| xtradb01 | `xtradb03,xtradb02` |
| xtradb02 | `xtradb03,xtradb01` |
| xtradb03 | `xtradb02,xtradb01` |

How Galera 4.17 (PXC 8.0.36) uses it, tested on a local 3-node cluster:

- **SST:** the first `SYNCED` node of the list; nodes that are down are skipped. If the listed nodes are busy, the
  joiner waits and retries (read in `gcs_group.cpp`, not tested).
- **IST:** whichever listed node still holds the missing write-sets and whose cache starts latest, whatever the order.
  It can be the read/write node, for example after it was reinstalled or got an SST.

No trailing comma: a name that matches no node makes the transfer fail (`No route to host`) instead of using any node.
The first node of the group (normally the read/write one) is still the last choice of the others.

The names must equal the host names (`wsrep_node_name`, from `network_mode: host`). `tasks/preflight.yml` checks this
as the first task of the XtraDB play, so a node that fails keeps its VIPs. It only checks the default list.

**Rule: deploy one node at a time (`--limit <node>`) until the host names of the environment have been read.** The
check runs per node (`serial`), so in a multi-node run a wrong name is found only after earlier nodes were deployed.
Read them with (read-only):

```bash
ansible -i nau-data/envs/<env>/hosts.ini xtradb_servers -m setup -a 'gather_subset=!all,min filter=ansible_nodename'
```

To use other names, set `xtradb_docker_wsrep_sst_donor` in the inventory or with `-e`; empty removes the line. Keep the
hosts in number order: a new node (xtradb04) becomes everyone's first donor and every node is recreated at its next
deploy.

## Container restarts and SST scratch

- `xtradb_docker_restart_policy` (`unless-stopped`): restarts after a reboot, not after a manual `docker stop`.
- `xtradb_docker_stop_timeout` (`180`): seconds to wait for a clean mysqld stop. Docker's default of 10 s can kill it,
  which can force an SST. Used for:
  - the container's `stop_grace_period`;
  - `docker-compose up -d --timeout`: without it, a recreate stops the old container with its own timeout (10 s for
    containers created before this setting);
  - `TimeoutStopSec` (+60 s) in `/etc/systemd/system/docker.service.d/xtradb-stop-timeout.conf`, since systemd's
    default 90 s would cut the stop on reboot. Only `daemon-reload` is run; Docker is not restarted.
- `xtradb_docker_tmp_path` (`/data/xtradb-tmp/`): the container's `/tmp`, so SST scratch (`pxc_sst_*`) lands on `/data`
  instead of the root disk.

An SST deletes the joiner's data directory and receives the copy into it, so `/data` needs room for about one copy of
the dataset. A killed SST leaves its `pxc_sst_*` directories behind: remove them while no SST runs.

Changing any of these or the donor list recreates the container at the next deploy; do it one node at a time.

## Example

Deploy first node, then join all other other nodes, then just run a normal deploy without the initialization.
Multi-node runs need the host names read first (see "State transfer donor").

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
