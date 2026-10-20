Nau playbooks
=============

This repository holds the specific playbooks required to manage the Open edX installation at NAU.

## Clone the required repositories
This repository uses another different repository.

The `secure-nau-data` repository is the private NAU repository where the keys and passwords are stored,
on per environment.

Commands to clone the dependencies:
```bash
git clone -b master git@github.com:fccn/secure-nau-data.git nau-data
git clone -b master git@github.com:fccn/nau_playbooks.git nau_playbooks
```

## Install Python 3.11

Because of the old version of Open edX that we use on NAU, we need to use the older Python 3.11 version.

Double check that you are using the Python 3.11 version, with:

```bash
python --version
```

To install the `pip` on the older Python version 3.11, run:

```bash
wget https://bootstrap.pypa.io/get-pip.py
python3.11 get-pip.py
```

## uv

```bash
uv venv --seed venv -p python3.11
```

## Installing OS packages
Some python pip dependencies or some ansible modules also require some operating system packages.
```bash
sudo apt install -y build-essential software-properties-common python3-software-properties curl git libxml2-dev libxslt1-dev libfreetype6-dev python3-pip python3-apt python3-dev tree libmysqlclient-dev libssl-dev libffi-dev python3-minimal
```

## Initializing Python Virtual Environment and Install dependencies

```bash
python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
ansible-galaxy install -p vendor/roles -r requirements.yml
```

## Run an ansible playbook

To run an ansible playbook, like for example the `deploy.yml` playbook, use a similar command:
```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit XPTO
```

## Run the firewall playbook

`firewall.yml` (re)applies the iptables firewall configuration, independent of `deploy.yml`. It
targets zero hosts unless `firewall_target` is passed:
```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini firewall.yml -e firewall_target=balancer_servers --check --diff
```

All firewall logic and configuration conventions are documented in `firewall.yml` itself — see its
header comment. Per-service ports/access rules are defined in `secure-nau-data`, so tightening or
adding access never requires a change here.

## Run the healthcheck playbook

`healthcheck.yml` checks the health of the whole platform. It only reads, it never changes anything,
and it fails (exit code 2) after printing the list of every problem found.

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini healthcheck.yml
```

| Tag | Where it runs | What it checks |
|-----|---------------|----------------|
| `vips` | all hosts | every keepalived virtual IP is held by exactly one node, and that node is its `MASTER` |
| `kubernetes` | control planes | rke2, API server `/readyz`, etcd quorum, leader and size, nodes Ready, pods, workloads and volume claims |
| `connectivity` | k8s workers | every worker reaches MongoDB, XtraDB (nodes and VIPs), Redis, Elasticsearch, ClickHouse, Richie MySQL and Ceph S3 |
| `docker-services` | load balancers, registry mirror | the `make healthcheck` of the service |
| `host` | all hosts | the OS, the IPv4 addresses against the inventory (`ansible_host`, `ansible_additional_ipv4`, `ansible_public_ipv4`, `old_ipv4`), the default route, container networks that overlap the host's, and the iptables rules loaded against the persisted file |
| `endpoints` | localhost | the public endpoints through each load balancer VIP, the DNS answer of the public names, flapping and TLS expiry |
| `vm` | all hosts | the previous healthcheck, with the retries that gate `deploy.yml` and the rolling playbooks |

Examples:
```bash
# Everything except the `vm` checks, which retry for up to 25 minutes
ansible-playbook -i nau-data/envs/<env>/hosts.ini healthcheck.yml --skip-tags vm

# Only some checks. Keep the `always` tag, it prints the report
ansible-playbook -i nau-data/envs/<env>/hosts.ini healthcheck.yml --tags vips,endpoints,always --skip-tags vm

# A node is in maintenance, so the VIPs do not need to be on their MASTER
ansible-playbook -i nau-data/envs/<env>/hosts.ini healthcheck.yml --skip-tags vm -e healthcheck_vip_expected_holder_enforced=false
```

The endpoints, the expected answers and the thresholds are in `group_vars/all/healthcheck.yml`.
Notes:
- The `host` checks also list the OS, kernel, addresses, default route and firewall summary of every host in the
  report (`healthcheck_host_show_info`). A host of a group in `firewall_managed_groups` must run the ansible-firewall
  rules: INPUT ends in a DROP, the persisted file (`/etc/iptables/rules.v4` or `/etc/sysconfig/iptables`, and the
  `v6` equivalents) is valid, and it ACCEPTs the same ports and source addresses as the rules loaded in the kernel
  (`-e healthcheck_host_firewall_expected=false` only reports them). Rules that jump to another chain (Docker,
  Kubernetes, fail2ban) are not compared. Use `healthcheck_host_unsupported_os` to flag end of life systems.
- With `--limit` only the hosts in the limit are checked, and only a VIP held by several nodes is
  reported. The `endpoints` checks run on `localhost`, so add it to the limit to run them.
- The `vm` checks stop the playbook at the first failing host, as the deploy playbooks need.
- The `kubernetes` checks run `etcdctl` when it is installed on the control planes, otherwise they rely
  on the etcd check of the API server `/readyz`.
- IPv6 is only tested with `-e healthcheck_endpoints_check_ipv6=true`, from a machine with IPv6.

## Using --check and --diff (Dry Run Mode)

When working with Ansible playbooks, it's a good practice to preview changes before applying them to your systems.
Two flags are particularly useful for this:

### --check flag
The `--check` flag runs the playbook in "dry-run" mode. It simulates the execution without actually making any changes to the target systems.
This allows you to see what tasks would be executed and catch potential errors before they happen.

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit XPTO --check
```

### --diff flag
The `--diff` flag shows the differences that would be made to files. When combined with `--check`, it displays what changes would occur without applying them.
This is particularly useful for tasks that modify configuration files, as you can see the exact line-by-line differences.

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit XPTO --diff
```

### Using both together (recommended for beginners)
For safety, always use both flags together when testing a playbook for the first time:

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit XPTO --check --diff
```

This combination will:
- Show you exactly what tasks would run
- Display file changes side-by-side
- Make no actual modifications to your systems

Once you're confident the changes are correct, run the playbook without these flags to apply the changes.

