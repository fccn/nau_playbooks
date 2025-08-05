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

## Install Python 3.8

Because of the old version of Open edX that we use on NAU, we need to use the older Python 3.8 version.

### Using package manager

So to execute the deployment process on newer Debian based Operating System like Ubuntu,
we need to add the additional `deadsnakes` Personal Package Archives (PPA) and
install the older Python 3.8 version.

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.8 python3.8-dev python3.8-venv python3.8-distutils
```

To install the `pip` on the older Python version 3.8, run:

```bash
wget https://bootstrap.pypa.io/get-pip.py
python3.8 get-pip.py
```

## uv

```bash
uv venv --seed venv -p python3.8.20
```

## Installing OS packages
Some python pip dependencies or some ansible modules also require some operating system packages.
```bash
sudo apt install -y build-essential software-properties-common python3-software-properties curl git libxml2-dev libxslt1-dev libfreetype6-dev python3-pip python3-apt python3-dev tree libmysqlclient-dev libssl-dev libffi-dev python3-minimal
```

## Initializing Python Virtual Environment and Install dependencies

```bash
python3.8 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
ansible-galaxy install -p vendor/roles -r requirements.yml
```

## Run an ansible playbook

To run an ansible playbook, like for example the `deploy.yml` playbook, use a similar command:
```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit XPTO
```
