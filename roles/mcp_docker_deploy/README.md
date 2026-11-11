# MCP server (nau-mcp) docker deploy

Deploys [nau-mcp](https://github.com/fccn/nau-mcp), the read-only MCP server that agents use to check the health of
the platform without being able to change anything. One VM per environment.

The Makefile and the compose file belong to the repository, because the server and the way it is run change together.
So this role does not template them: it prepares the VM, **pulls the repository at a pinned version** and calls the
targets of `deploy/Makefile` of that clone.

It is the "Deploy MCP servers" play of `deploy.yml`, which installs Docker with `geerlingguy.docker` first, like the other
Docker plays.

```
MCP VM
  /nau/ops/nau-mcp              the clone, at the pinned version (a detached HEAD)
    deploy/                     Makefile, docker-compose.yml, .env (no secrets), secrets/, secrets-grafana/, logs/
  nau-mcp container             listens on 127.0.0.1 only: agents reach it through an SSH tunnel
  nau-mcp-grafana container     only where a Grafana token is defined
```

## What it does, on each VM, in order

1. Validates the variables (see below). The play of `deploy.yml` does this first, before Docker is installed or configured, so a
   wrong variable stops it before anything is changed; the role does it again so it is safe used on its own. The deploy key and
   the Grafana token are never printed.
2. Installs `git` and `make`.
3. Writes the SSH host key that GitHub publishes into the `known_hosts` of root.
4. Pulls the repository at `mcp_git_version`, with the deploy key. The key is written to a temporary file of mode `0600`
   and removed right after, also when the pull fails.
5. `make init ENV=<mcp_environment>`: creates `.env`, `secrets/`, `logs/` and `certs/`. It refuses to change the
   environment of a VM that already has one.
6. `make image`: builds the image from the pulled code, on the VM.
7. Where `mcp_grafana_token` is defined: `make grafana-init` when it differs from the one on the VM or the setup is
   incomplete, then the owner and the modes of the Grafana secret files are enforced.
8. `make deploy`, only when the pulled code, the image or the Grafana setup changed, or when the server is not healthy.
9. Waits until `make healthcheck` passes, and shows `make status`.

## Required variables

Define them per environment in `secure-nau-data` (`envs/<env>/group_vars/mcp_servers.yml`):

```yaml
mcp_environment: dev          # dev, stage or prod: environments/<mcp_environment>.yaml of the repository
mcp_git_version: v1.2.3       # a tag or a full 40-character commit, never a branch
mcp_git_ssh_key: |            # read-only deploy key of the repository, OpenSSH format
  -----BEGIN OPENSSH PRIVATE KEY-----
  ...
  -----END OPENSSH PRIVATE KEY-----
```

- **Version.** A branch is refused, so that a deploy is always the same code. To update the server, change this value.
- **Deploy key.** One per environment, so each can be revoked on its own:
  `ssh-keygen -t ed25519 -N '' -C 'nau-mcp deploy key <env>' -f key`. Add `key.pub` to the repository
  (Settings, Deploy keys) with "Allow write access" **unticked**, put `key` in `secure-nau-data`, and keep a copy in the
  NAU password database. The value committed in `secure-nau-data` is a placeholder that fails the validation on purpose: the play
  stops at its first task, before Docker. A run with `--tags snmpd` only does not validate.
- **Environment.** `make init` refuses to change it afterwards, so a typo cannot turn a VM into another environment.

### Optional: the Grafana tools

```yaml
mcp_grafana_token: <token>    # token of a Viewer (read-only) service account of the Grafana of this environment
```

Defined and valid (20 to 200 characters), it switches the Grafana tools on. Create the service account with the **Viewer**
role and a token **with an expiry**: Grafana's default is "Never".

**Where the token lives**, in the way of the other docker roles: the value in `secure-nau-data`, a file in the folder of
the service that belongs to the user of the container and that nobody else can read, mounted read-only into the container,
and never an environment variable or a command line.

| What | Where on the VM | Owner and mode |
|---|---|---|
| The token | `deploy/secrets-grafana/token`, mounted read-only into the Grafana container | the container user, `0600`, in a `0700` folder |
| The secret that the two containers share (random, made by `make grafana-init`) | `deploy/secrets/grafana-mcp-token` | the container user, `0600` |

The role passes the token through the stdin of `make grafana-init`, so it is on no command line and the tasks that carry it
have `no_log`. It does that only when the value differs from the one on the VM or the setup is incomplete. On every run it
also puts the owner (the one of `secrets/`, which `make init` made for the container user) and the modes of those files back
where they should be, as the other roles do with the `owner` and `mode` of a secret: a Grafana container that cannot read
its token fails its healthcheck.

To rotate the token, change the value and deploy again: the containers are recreated. Without Ansible, the repository has
the same hand-over: in `deploy/`, `read -rsp 'Grafana token: ' GRAFANA_TOKEN; export GRAFANA_TOKEN; make grafana-init`.
Not defined, the Grafana tools stay as they are on the VM (a message says so).

## Deploy

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit mcp_servers -e mcp_deploy=true --tags mcp
```

`--tags mcp` runs only Docker and this role. Without it the play also runs the base plays of every NAU host (users, the
root SSH keys, the hosts file, ...), which is what a new VM needs once, but replaces whatever else is in its root
`authorized_keys`.

Preview it first. In check mode the packages, the folders and the host key are previewed, and the pull, the build and the
deploy are announced and not run, because they need the repository:

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit mcp_servers -e mcp_deploy=true --tags mcp --check --diff
```

Running it again changes nothing: the recap says `changed=0` and the server is not restarted. The containers are recreated
only when the pulled code, the image or the Grafana token changed, or when the server was not healthy.

### Check it

```bash
cd /nau/ops/nau-mcp/deploy && make status && make healthcheck
```

`scripts/verify-deployment.sh` of the repository checks it the way an agent uses it.

### Tokens of the agents

They are not managed by this role. They are created on the VM, shown once, and revoked there:
`make token-create USER_NAME=<who>`, `make token-list`, `make token-revoke ID=<id>`. A fresh VM has none, so it refuses
every request until the first one is created.

## Monitoring and the firewall

Both are opt-in, in `secure-nau-data`:

```yaml
mcp_snmpd_configs:
  - extend mcp_healthcheck /usr/bin/make --jobs 20 --no-print-directory --directory /nau/ops/nau-mcp/deploy silent-healthcheck
mcp_makefile_healthcheck: [ "/nau/ops/nau-mcp/deploy" ]
```

- **snmpd.** The play imports `ansible-snmpd` only where `mcp_snmpd_configs` is defined (`--tags snmpd` runs just that).
  That role adds the snmpd user to the `docker` group, which is root-equivalent on a VM that holds read access to the
  platform. The Icinga service that reads the `extend` has to be created in Icinga.
- **`mcp_makefile_healthcheck`.** The `healthcheck`, `upgrade_and_reboot`, `rolling_execute` and `server_maintenance`
  playbooks then wait for the server after a reboot. Switch it on only once the server is deployed on that VM: until then
  they retry for up to 25 minutes (50 times, every 30 seconds) because the folder is not there.
- **Firewall.** This role opens nothing: the server listens on the loopback only. If a group enables
  `mcp_servers_firewall_ports` in `secure-nau-data`, SSH from the management hosts is the only port it needs.

## A VM that was installed by hand

The first run of this role on a VM that follows the installation guide of the repository takes it over: the origin of the
clone becomes `mcp_git_repo`, the clone is left on the pinned commit (a detached HEAD), the Docker settings of
`group_vars/all/docker.yml` replace `/etc/docker/daemon.json` (Docker restarts once if it differs) and the containers are
recreated once. `.env`, the tokens and the logs are kept. A second run changes nothing.

## Variables

| Variable | Default | What |
|---|---|---|
| `mcp_environment` | required | `dev`, `stage` or `prod` |
| `mcp_git_version` | required | tag or full commit |
| `mcp_git_ssh_key` | required | read-only deploy key, OpenSSH format |
| `mcp_grafana_token` | not defined | token of a Viewer service account; switches the Grafana tools on |
| `mcp_git_repo` | `git@github.com:fccn/nau-mcp.git` | repository, over SSH |
| `mcp_docker_deploy_base_folder` | `/nau/ops/nau-mcp` | the clone; `deploy/` inside it is where `make` runs |
| `mcp_git_host_key` | GitHub's `ssh-ed25519` key | checked on every pull |
| `mcp_git_known_hosts_file` | `/root/.ssh/known_hosts` | where the host key is written |
| `mcp_image_build_timeout` | `1800` | seconds the build may take (the first one downloads the dependencies) |
| `mcp_healthcheck_retries` / `_delay` | `24` / `5` | wait for the server to be healthy (about 2 minutes) |

## Notes

- **Why not the git of `ansible-docker-deploy`.** It pulls with `accept_hostkey`, which is `StrictHostKeyChecking=no`: it
  also accepts a *changed* host key. This server runs what it pulls, so the published key of GitHub is pinned and the pull
  refuses any other. If GitHub rotates it, replace `mcp_git_host_key` with the new one from
  <https://api.github.com/meta> (`ssh_keys`).
- **The image build.** It happens on the VM, so the VM needs Docker Hub (or the registry mirror that the Docker settings
  name) and PyPI. The first build takes a minute or two, the next ones seconds. The role compares the layers and the
  creation time of the image before and after, not its ID: with the containerd image store every build gets a new ID.
  Images of older versions stay until `clean.yml` prunes them.
- **Logs.** The compose file of the repository sets its own rotated `json-file` logging for both containers, so they do
  not depend on the `fluentd` default of the Docker settings.
- **Secrets.** The key and the token are `no_log` and never reach a log, also with `-vvv`. A failed `make grafana-init`
  is reported with what `make` printed, which never holds the token.

## Remove it

```bash
cd /nau/ops/nau-mcp/deploy && make grafana-disable   # only where the Grafana tools are on
docker compose down && cd / && rm -rf /nau/ops/nau-mcp
```
