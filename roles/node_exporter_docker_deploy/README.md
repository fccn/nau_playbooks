# Node exporter docker deploy

Deploys the Prometheus [`node_exporter`](https://github.com/prometheus/node_exporter) on a VM, so the Prometheus/Grafana
of the Kubernetes cluster can show its CPU, memory, disk and network. It is used by the "Deploy to XtraDB database" play
of `deploy.yml`, after the exporter of the XtraDB and with no password to set, **only in the environments where
`node_exporter_enabled` is true** (see "Enable it per environment").

```
VM
  node-exporter   :9100  <--- Prometheus (k8s) scrapes this
```

It never touches other containers. It runs as `nobody`, with a read-only root, no capabilities and 128 MB of memory.
It uses the host network and processes, and mounts `/` read-only so it can report the disks mounted under it, for example `/data`.

## What it does, on each node, in order

1. Creates `/nau/ops/node-exporter` with the `Makefile` and the `docker-compose.yml`.
2. Starts the container, through the `ansible-docker-deploy` role.
3. Waits until `http://<node>:9100/metrics` answers.

In check mode on a node that has no exporter yet, only the folder is reported: the container is deployed after the folder exists.

## Enable it per environment

Set it in `secure-nau-data`, `envs/<env>/group_vars/xtradb_servers.yml`:

```yaml
node_exporter_enabled: true
```

- Without it (or `false`), a full XtraDB deploy does not deploy the node exporter, and the snmpd step does not add its
  `extend`. Add it to an environment only when you are ready to deploy there, because a failure of the node exporter
  stops the rolling XtraDB deploy (see below).
- `--tags node_exporter` deploys it anyway, on purpose, like `--tags xtradb_exporter` does for the exporter of the XtraDB.
  Without the flag the snmpd step does not monitor it, so set the flag once it is deployed.
- Do not set a default for it in this repository's `group_vars`: those win over `secure-nau-data`, so a default there would
  hide the per-environment value. The playbook reads it as `node_exporter_enabled | default(false)` (`node_exporter_configured`).
- Setting it back to `false` does not remove the container, it only stops the deploys and, at the next snmpd step, removes
  the `extend`. To remove it, see the end of this file.

## Usage

```bash
# with the XtraDB deploy
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit xtradb_servers -e xtradb_deploy=true
# only the node exporter, last node first
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers[-1]' -e xtradb_deploy=true --tags node_exporter
```

On the node, `make healthcheck` in `/nau/ops/node-exporter` checks the container and the metrics.

If it fails on a node (for example port 9100 is already in use), the rolling XtraDB deploy stops there, before the remaining
nodes, like any other failure of that play. The database of that node is already deployed and keepalived is already restored.
Fix it and carry on with the remaining nodes, or leave both exporters out:

```bash
# the remaining nodes only
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit <remaining nodes> -e xtradb_deploy=true
# deploy the databases without the exporters (the tags of this role and of the XtraDB exporter)
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit xtradb_servers -e xtradb_deploy=true --skip-tags node_exporter,xtradb_exporter
```

## Monitoring with SNMP (Icinga)

`group_vars/xtradb_servers.yml` adds an `extend` to the snmpd configuration of the XtraDB nodes, like the other roles do.
It prints `OK` when `make healthcheck` passes, and no `OK` (and a non-zero exit code) when the container is stopped or the
metrics do not answer:

```bash
snmpwalk -v 2c -c <community> <node> 'NET-SNMP-EXTEND-MIB::nsExtendOutputFull."node_exporter_healthcheck"'
```

- It reaches the node with the snmpd step of the XtraDB play, which runs with `-e xtradb_deploy=true` and no tag or with
  `--tags snmpd`. A run with only `--tags node_exporter` does not touch snmpd.
- **The Icinga service that reads it has to be created in Icinga**, it is not part of this repository.
- The folder is `0755` so that snmpd, which runs the check as its own user, can enter it.
- The check is not added to `makefile_healthcheck` on purpose. That list is waited on for up to 25 minutes by the maintenance
  playbooks, so a dead metrics exporter would block the maintenance of the database nodes.
- `node_exporter_docker_deploy_base_folder` is also defined in `group_vars/xtradb_servers.yml`. The XtraDB play imports this role
  statically, so its default is visible there, but `snmpd_configs` is also evaluated outside that play: in another play,
  in an ad-hoc `ansible -m debug -a var=snmpd_configs`, or when a later change moves the snmpd step. Without the copy those
  fail with `'node_exporter_docker_deploy_base_folder' is undefined` (tested).

## Notes

- It listens only on the VM IP (`node_exporter_listen_ip`, default `ansible_host`), with no auth or TLS. The port has to be
  reachable from the Prometheus pods. `xtradb_servers_firewall_ports` is commented out in every environment today, so 9100 is
  open; if that list is ever enabled, add 9100 next to the 9104 of the XtraDB exporter (the commented example in
  `secure-nau-data` has both).
- Only the collectors in `node_exporter_collectors` are enabled (CPU, memory, filesystem, disks, load, network, uname, stat, vmstat, pressure).
  `pressure` reads `/proc/pressure` (kernel 4.20+; the XtraDB VMs run 5.15) and shows how long tasks waited for CPU, memory or I/O.
  The filesystem metrics also include `tmpfs` mounts, filter by `fstype` in the queries.
- A crash does not restart it forever: `on-failure:5`, then it stays `Exited`, so it never blocks the deploy of the other roles.
  `stop_signal: SIGKILL` makes a normal stop exit with 137, so Docker brings it back after a reboot.
- The image is pinned. Read the CHANGELOG of `node_exporter` before upgrading.
- **One `ERROR` line in the log on every start is expected.** `docker logs node-exporter` shows
  `level=ERROR source=diskstats_linux.go:255 msg="Failed to open directory, disabling udev device properties" collector=diskstats path=/run/udev/data`.
  The container has no `/run/udev`, so the disk collector skips the udev properties, and the disk metrics are exposed as usual.
  Mounting `/run/udev` would remove the line but give the container more of the host for no metric the dashboards use.

## Remove it

Set `node_exporter_enabled: false` (or remove it) for the environment in `secure-nau-data`, so the next deploy does not bring
it back, and run the snmpd step (`--tags snmpd`) so the `extend` goes away. Then, on each node:

```bash
cd /nau/ops/node-exporter && docker-compose down && cd / && rm -rf /nau/ops/node-exporter
```
