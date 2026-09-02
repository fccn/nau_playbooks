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

The `firewall.yml` playbook (re)applies the iptables firewall configuration on any host, and can
be run independently of `deploy.yml`:
```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini firewall.yml --limit XPTO --check --diff
```

All firewall logic lives in this single file. No IP address, CIDR, hostname, port number, or
knowledge of which service talks to which other service is hardcoded in it — all of that is
data-driven from `secure-nau-data`.

### `<group_name>_firewall_ports`

For each inventory group, `secure-nau-data` may define a `<group_name>_firewall_ports` list, one
entry per port that group's service should accept connections on:
```yaml
xtradb_servers_firewall_ports:
  - port: "{{ xtradb_mysql_port }}"
    comment: "XtraDB MySQL client port"
    allowed_ips: []                          # falls back to nau_network
  - port: "{{ xtradb_galera_sst_port }}"
    comment: "XtraDB Galera SST"
    allowed_ips: "{{ xtradb_servers_ips }}"  # own cluster peers only

balancer_servers_firewall_ports:
  - port: 22
    comment: "SSH from management hosts"
    allowed_ips: ["203.0.113.10", "203.0.113.11"]
    interface: eth1                          # optional: restrict the rule to one interface
```

Each entry's source address is resolved in order:
1. Its own `allowed_ips` and/or `allowed_network`, combined if either or both are defined.
2. Otherwise, the shared `nau_network` variable (defined once under `group_vars/all`).
3. Otherwise, that entry's rule is **dropped**. This denies rather than allows: the
   `ansible-firewall` role always ends its ruleset with a catch-all DROP. A task at the start of
   `firewall.yml` warns if `nau_network` is undefined, since that silently denies every rule
   relying on it as a fallback.

An entry may also set an optional `interface` key (e.g. `interface: eth1`) to restrict that rule to
a specific network interface. If omitted, the rule applies regardless of interface.

Since each entry carries its own allow-list, different ports on the same service can have different
access levels (e.g. a broadly-open client port alongside cluster-internal ports restricted to that
service's own peers) — there's no need for `firewall.yml` to know or care about this distinction.

### Groups with no `_firewall_ports` defined yet

If a group has no `<group_name>_firewall_ports` list at all, it instead gets a single default
rule: open to `nau_network`, with no port restriction. This matches today's unrestricted internal
access, so adopting this playbook doesn't tighten anything until you explicitly opt a service in.

### Adding or tightening a service's access

Everything about a service's firewall exposure — which ports are open and who's allowed to reach
them — is defined entirely in that service's own file in `secure-nau-data`. To tighten or loosen
access, or to add a brand-new service, add/edit its `<group_name>_firewall_ports` list there.
**No change to `firewall.yml` is ever needed** for this, regardless of how many ports a service
has or how differently they need to be restricted.

Rules should only be defined at the most specific (leaf) inventory group level, never at a parent
`:children` group too — a host belonging to both would otherwise get both sets of rules aggregated
together.

`--limit` works as expected: it only restricts which hosts the play runs against, not group
membership resolution.

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

