Nau playbooks
=============

This repository holds the specific playbooks required to manage the open edX installation at NAU.


Initializing the ops stack
==========================

```
git clone -b open-release/hawthorn.master https://github.com/edx/configuration.git configuration
git clone -b master git@gitlab.fccn.pt:nau/nau_playbooks.git nau_playbooks
git clone -b master git@gitlab.fccn.pt:nau/secure-nau-data.git nau-data

virtualenv venv_ops
source venv_ops/bin/activate

sudo apt-get install -y build-essential software-properties-common python-software-properties curl git-core libxml2-dev libxslt1-dev libfreetype6-dev python-pip python-apt python-dev tree libmysqlclient-dev libssl-dev libffi-dev python-minimal virtualenv


pip install -r configuration/requirements.txt
```
