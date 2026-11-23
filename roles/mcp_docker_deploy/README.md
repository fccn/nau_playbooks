# MCP server docker deploy

Deploys the NAU MCP server: the official Grafana MCP server ([`grafana/mcp-grafana`](https://github.com/grafana/mcp-grafana),
Apache-2.0), configured to only read, on the loopback address of one VM per environment. Agents reach it through an SSH
tunnel and present the agent token: see [Connect an agent](#connect-an-agent).

The compose file and the Makefile are templates of this role (`templates/`); the values of each environment come from
`secure-nau-data`. The role:

1. checks its variables (`tasks/validate.yml`; the play of `deploy.yml` runs it before Docker is installed, so a placeholder
   or a wrong value stops the run before anything changes);
2. writes the two tokens in `secrets/` of the folder of the deploy (mode 600 in a folder of mode 700, owned by the
   container's user, uid 10001), never printed and never in a `--diff`;
3. hands over to `ansible-docker-deploy`, which templates `docker-compose.yml`, the `Makefile` and `smoke.py`, pulls the
   pinned image and starts the server with `make deploy`, or `make restart` when the agent token changed;
4. waits for `make healthcheck`.

The play of `deploy.yml` installs Docker first (`geerlingguy.docker`, with the shared settings of
`group_vars/all/docker.yml`), and snmpd where `mcp_snmpd_configs` is defined.

## Required variables

In `secure-nau-data`, `envs/<env>/group_vars/mcp_servers.yml`:

| Variable | What |
|---|---|
| `mcp_grafana_url` | The Grafana of the environment, `https://...`. |
| `sa_read_grafana_token` | The token of a service account with the **Viewer** role in that Grafana. |
| `mcp_agent_token` | The token that agents present, 32 characters or more: `openssl rand -base64 32`, or longer. Keep a copy in the NAU password database: the people who connect agents need it. |

A placeholder in any of them fails the validation on purpose.

## How it stays read-only

The flags of the command in `templates/docker-compose.yml.j2` are fixed, not variables:

- `--disable-write`, and only six categories of tools (`search`, `datasource`, `prometheus`, `loki`, `alerting`,
  `dashboard`): 25 tools, all marked read-only. Queries are limited to 24 hours, 1,500 points per series and 100 log lines.
- It listens on `127.0.0.1` only, and accepts only `127.0.0.1:<port>` and `localhost:<port>` as `Host`. A call without the
  agent token gets 401, and the server does not start without one.
- The Grafana token is the one of a Viewer service account: Grafana itself refuses any change.
- The container: uid 10001, read-only filesystem, no capabilities, limits on memory, CPU and processes, capped logs.

Change them only after reading the release notes of the image and testing on DEV.

## Deploy

Preview, then run the same without `--check --diff`:

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit mcp_servers -e mcp_deploy=true --tags mcp --check --diff
```

Keep `--limit mcp_servers --tags mcp`: a run of `deploy.yml` without them also applies the base plays, which manage users and
the root keys of every host.

Check mode starts nothing. On a VM that is already deployed it shows the diff of `docker-compose.yml`, the `Makefile` and
`smoke.py`, and says whether a token would change, without its value; on a new VM it can only say that the folder is not
there yet.

A run with no change does not restart the server. Two steps of `ansible-docker-deploy` (the pull of the image and the start
command) always report `changed`, as in the other docker deploys.

## Tokens

To change one, change it in `secure-nau-data` and deploy. A new Grafana token is written to its file and read on the next
call, without a restart. A new agent token recreates the container (`make restart`), because the server reads it when it
starts: tell the people who use the old one. `make deploy` also recreates the container while the token file is newer than
it, so a deploy that failed after writing a new token applies it on the next run.

## Check it

On the VM, in `/nau/ops/nau-mcp`: `make status`, `make healthcheck`, and `make smoke` (as root) to act like an agent: a call
without the token is refused, the handshake, the tools (all marked read-only), and one read from Grafana.

## Connect an agent

1. Open a tunnel to the VM and leave it running. The names of the gateway and of the MCP VMs are in the NAU technical
   documentation. Keep the local port the same as the one on the VM (8443 by default): the server checks the `Host` of each
   request.

   ```bash
   ssh -N -L 8443:127.0.0.1:8443 -J <user>@<gateway>:<port> root@<mcp-vm>
   ```

2. Give the token to the agent through an environment variable, never on a command line or in a committed file. The token
   is `mcp_agent_token` of the environment, in `secure-nau-data` and in the NAU password database.

   ```bash
   read -rsp 'NAU MCP token: ' NAU_MCP_TOKEN; export NAU_MCP_TOKEN
   ```

3. Add the server to the agent's client. Name it after its environment (`nau-dev`): the model sees the name, and it tells
   which environment an answer is about. The single quotes keep `${NAU_MCP_TOKEN}` for the client to expand.

   ```bash
   # GitHub Copilot CLI: the entry goes to ~/.copilot/mcp-config.json
   copilot mcp add --transport http --header 'Authorization: Bearer ${NAU_MCP_TOKEN}' nau-dev http://127.0.0.1:8443/mcp

   # Claude Code
   claude mcp add --transport http nau-dev http://127.0.0.1:8443/mcp --header 'Authorization: Bearer ${NAU_MCP_TOKEN}'
   ```

   VS Code (`.vscode/mcp.json`, or *MCP: Open User Configuration*) asks for the token once and keeps it:

   ```json
   {
     "inputs": [{ "type": "promptString", "id": "nau-mcp-token", "description": "NAU MCP token", "password": true }],
     "servers": {
       "nau-dev": {
         "type": "http",
         "url": "http://127.0.0.1:8443/mcp",
         "headers": { "Authorization": "Bearer ${input:nau-mcp-token}" }
       }
     }
   }
   ```

4. Check the path before you blame the agent. With the tunnel open and the token exported, from a checkout of
   nau_playbooks (or with the copy in the folder of the deploy on the VM):

   ```bash
   python3 roles/mcp_docker_deploy/templates/smoke.py    # http://127.0.0.1:8443/mcp by default
   ```

   It does what an agent does, and says what happened at every step: a call without the token is refused, the
   handshake, the tools (all marked read-only) and one read from Grafana (`list_datasources`). It changes nothing.

5. Ask the agent something small first: *"With the nau-dev MCP server, list the Grafana data sources and check their health."*

Copilot CLI marks the server `needs-auth` when it answers `401` (the token did not arrive, or it is not the current one).
Do not list `NAU_MCP_TOKEN` in its `--secret-env-vars`: the CLI would strip it before it fills in the header.

## Upgrade the image

1. Read the release notes of `grafana/mcp-grafana` since the pinned version: new or renamed flags and tools, changed
   defaults, security fixes.
2. Pull the new version and take its digest:
   `docker pull grafana/mcp-grafana:<version> && docker inspect -f '{{index .RepoDigests 0}}' grafana/mcp-grafana:<version>`.
   Check that every flag of the command of the compose template still exists: `docker run --rm grafana/mcp-grafana:<version> --help`.
3. Try it on DEV first: set `mcp_docker_image: grafana/mcp-grafana:<version>@sha256:<digest>` in the DEV
   `mcp_servers.yml` of `secure-nau-data`, deploy, and run `make smoke`: it lists the tools and fails if one is not
   read-only.
4. Then change the default in `defaults/main.yml`, and remove the DEV override.

## Monitoring and the firewall

Both are opt-in, in `secure-nau-data`:

```yaml
mcp_snmpd_configs:
  - extend mcp_healthcheck /usr/bin/make --jobs 20 --no-print-directory --directory /nau/ops/nau-mcp silent-healthcheck
mcp_makefile_healthcheck: [ "/nau/ops/nau-mcp" ]
```

- **snmpd.** The play imports `ansible-snmpd` only where `mcp_snmpd_configs` is defined (the deploy command with
  `--tags snmpd` instead of `--tags mcp` runs just that; it still needs `-e mcp_deploy=true`).
  That role adds the snmpd user to the `docker` group, which is root-equivalent on a VM that holds read access to the
  platform. The Icinga service that reads the `extend` has to be created in Icinga.
  **Test the `extend` as the snmpd user before relying on it**:
  `sudo -u Debian-snmp /usr/bin/make --jobs 20 --no-print-directory --directory /nau/ops/nau-mcp silent-healthcheck`
  must print `OK`. It needs the `docker` group, not `secrets/`. snmpd only gets the group when it is restarted after its
  user joined it, so also read the `extend` through snmpd.
- **`mcp_makefile_healthcheck`.** The `healthcheck`, `upgrade_and_reboot`, `rolling_execute` and `server_maintenance`
  playbooks then wait for the server after a reboot. Switch it on only once the server is deployed on that VM: until then
  they retry for up to 25 minutes (50 times, every 30 seconds) because the folder is not there.
- **Firewall.** This role opens nothing: the server listens on the loopback only. If a group enables
  `mcp_servers_firewall_ports` in `secure-nau-data`, SSH is the only port it needs.

## Limits

- **One Grafana per environment.** Another Grafana (the analytics one, for example) is not covered.
- **Logs.** NAU's logs are in VictoriaLogs, shown in Grafana by the `victorialogs-datasource` plugin. The server only
  selects its VictoriaLogs support for the newer plugin id (`victoriametrics-logs-datasource`, plugin v0.13.0 and later). With
  an older plugin, searching logs works, and label discovery and LogsQL `stats` do not.
- **One agent token per environment.** There is no record per person: Grafana sees the service account, and the SSH log of
  the VM shows who opened a tunnel.
- **The tunnel logs in as root.** A user that can only open the tunnel (`permitopen="127.0.0.1:8443"` on its key, no shell)
  would be less privileged; it needs that user and its keys in `secure-nau-data`.
- **A caller's own Grafana token.** A caller that holds the agent token may send another Grafana token in the
  `X-Grafana-Service-Account-Token` header, and the server uses it instead of the Viewer one for that call. Nothing can be
  written that way (no tool writes), but reads follow the rights of that token.
- **A Viewer can write log lines through Grafana.** Grafana's data source proxy lets any Viewer token reach the ingestion
  endpoint of VictoriaLogs, which has no authentication of its own. No tool of this server uses that proxy, and the token
  never leaves the container.
- **24 hours** of history per query. A longer one needs Grafana itself.

## Variables

| Variable | Default | What |
|---|---|---|
| `mcp_grafana_url`, `sa_read_grafana_token`, `mcp_agent_token` | required | see above |
| `mcp_docker_image` | `grafana/mcp-grafana:2.2.0@sha256:...` | the image, pinned by digest (the validation refuses one without) |
| `mcp_docker_container_name` | `nau-mcp-grafana` | |
| `mcp_port` | `8443` | the port on `127.0.0.1`; agents use the same one at their end of the tunnel |
| `mcp_docker_deploy_base_folder` | `/nau/ops/nau-mcp` | the folder of the deploy, where `make` runs |
| `mcp_docker_deploy_uid` | `10001` | the container's user, owner of `secrets/` |
| `mcp_docker_deploy_compose_template`, `mcp_docker_deploy_templates` | `templates/` | what `ansible-docker-deploy` templates |
| `mcp_docker_deploy_healthcheck_retries` / `_delay` | `24` / `5` | wait for the server to be healthy (about 2 minutes) |

## Notes

- **Why the tokens are not templates of `ansible-docker-deploy`.** Its template task has no `no_log`, so a `--diff` would
  show them. This role writes them with `no_log` and without a diff; they never reach a log, also with `-vvv`.
- **The image.** It is pulled from Docker Hub (or the registry mirror of the Docker settings); nothing is built on the VM.
  Images of older versions stay until `clean.yml` prunes them.
- **Logs.** The compose file sets its own rotated `json-file` logging, so it does not depend on the `fluentd` default of
  the Docker settings.
- **`smoke.py`** has no template variable: it is the same file on the VM and in a checkout of nau_playbooks, from which
  users run it on their workstations. It needs only Python's standard library.

## Remove it

```bash
cd /nau/ops/nau-mcp && make stop && cd / && rm -rf /nau/ops/nau-mcp
```
