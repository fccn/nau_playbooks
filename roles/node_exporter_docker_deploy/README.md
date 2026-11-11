# Node exporter docker deploy

Deploys the Prometheus [`node_exporter`](https://github.com/prometheus/node_exporter) on a VM, so the Prometheus/Grafana
of the Kubernetes cluster can show its CPU, memory, disk and network. It is used by the "Deploy to XtraDB database" play
of `deploy.yml`, after the exporter of the XtraDB and with no password to set.

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

## Usage

```bash
# with the XtraDB deploy
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit xtradb_servers -e xtradb_deploy=true
# only the node exporter, last node first
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers[-1]' -e xtradb_deploy=true --tags node_exporter
```

On the node, `make healthcheck` in `/nau/ops/node-exporter` checks the container and the metrics.

## Notes

- It listens only on the VM IP (`node_exporter_listen_ip`, default `ansible_host`), with no auth or TLS. The port has to be
  reachable from the Prometheus pods.
- Only the collectors in `node_exporter_collectors` are enabled (CPU, memory, filesystem, disks, load, network, uname, stat, vmstat).
  The filesystem metrics also include `tmpfs` mounts, filter by `fstype` in the queries.
- A crash does not restart it forever: `on-failure:5`, then it stays `Exited`, so it never blocks the deploy of the other roles.
  `stop_signal: SIGKILL` makes a normal stop exit with 137, so Docker brings it back after a reboot.
- The image is pinned. Read the CHANGELOG of `node_exporter` before upgrading.
