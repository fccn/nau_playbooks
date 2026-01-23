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

