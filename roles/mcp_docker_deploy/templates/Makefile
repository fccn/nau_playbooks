# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to operate the NAU MCP server: run `make` in this folder for the list of targets.
# The deploy (roles/mcp_docker_deploy) runs `make deploy`, or `make restart` when the agent token changed, then
# `make healthcheck`.
###################################################################################################

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE   := docker compose
CONTAINER := {{ mcp_docker_container_name }}
# The user of the container: it owns secrets/.
UID_GID   := {{ mcp_docker_deploy_uid }}
PORT      := {{ mcp_port }}

help: ## list the targets
	@grep -E '^[a-zA-Z0-9_%-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-22s %s\n", $$1, $$2}'
.PHONY: help

check: ## the secrets that a start needs (prints no value; as root)
	@test "$$(stat -c '%a %u' secrets 2>/dev/null)" = "700 $(UID_GID)" || { echo "check: secrets/ must exist, with mode 700 and owner uid $(UID_GID)"; exit 1; }
	@for f in secrets/grafana-token secrets/agent-token; do \
	  test -s "$$f" || { echo "check: $$f is missing or empty (the deploy writes it)"; exit 1; }; \
	  test "$$(stat -c '%a %u' "$$f")" = "600 $(UID_GID)" || { echo "check: $$f must have mode 600 and owner uid $(UID_GID)"; exit 1; }; \
	done
	@echo "check: OK"
.PHONY: check

# The server reads the agent token when it starts, so deploy also recreates the container when the token file is newer
# than the container's start (a deploy that failed after writing the token). Whole seconds: the same second counts as newer.
deploy: check ## start the server, or update it: the container is recreated when its settings changed or the agent token is newer than it
	@started=$$(docker inspect -f {% raw %}'{{.State.StartedAt}}'{% endraw %} $(CONTAINER) 2>/dev/null) || started=; \
	recreate=; \
	if [ -n "$$started" ]; then \
	  started=$$(date -d "$$started" +%s 2>/dev/null) || started=0; \
	  if [ "$$(stat -c %Y secrets/agent-token)" -ge "$$started" ]; then \
	    echo "deploy: the agent token is newer than the container: recreating it"; recreate=--force-recreate; \
	  fi; \
	fi; \
	$(COMPOSE) up -d --remove-orphans $$recreate
.PHONY: deploy

restart: check ## recreate the container, so that the server reads the agent token again (a new Grafana token needs nothing)
	$(COMPOSE) up -d --remove-orphans --force-recreate
.PHONY: restart

stop: ## stop and remove the container (the files of this folder stay)
	$(COMPOSE) down
.PHONY: stop

status: ## the container, its health, the image and the Grafana it reads
	@if docker inspect $(CONTAINER) >/dev/null 2>&1; then \
	  docker inspect -f {% raw %}'container : {{.State.Status}}, health {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}, started {{.State.StartedAt}}, restarts {{.RestartCount}}'{% endraw %} $(CONTAINER); \
	  docker inspect -f {% raw %}'image     : {{.Config.Image}}'{% endraw %} $(CONTAINER); \
	else echo "container : not created (make deploy)"; fi
	@echo "grafana   : {{ mcp_grafana_url }}"
.PHONY: status

logs: ## follow the logs, without the refused call that the health check makes every 30 s (see logs-all)
	docker logs -f --tail 100 $(CONTAINER) 2>&1 | grep --line-buffered -v 'reason="missing bearer token"'
.PHONY: logs

logs-all: ## follow the logs, all of them: an agent that forgot its token also shows as "missing bearer token"
	docker logs -f --tail 100 $(CONTAINER)
.PHONY: logs-all

smoke: ## act like an agent: a call without the token is refused, the handshake, the tools, one read from Grafana (as root)
	@NAU_MCP_TOKEN_FILE=secrets/agent-token python3 smoke.py http://127.0.0.1:$(PORT)/mcp
.PHONY: smoke

healthcheck-container: ## the container runs and its health check passes: /healthz answers and a call without the token gets 401
	@test "$$(docker inspect -f {% raw %}'{{if .State.Health}}{{.State.Health.Status}}{{end}}'{% endraw %} $(CONTAINER) 2>/dev/null)" = "healthy" || { echo "Check $(CONTAINER) container: error!"; exit 1; }
	@echo "Check $(CONTAINER) container: OK"
.PHONY: healthcheck-container

healthcheck: healthcheck-container ## overall health check (it contacts nothing outside the VM)
	@echo "Everything looks: OK"
.PHONY: healthcheck

# A target in silent mode, for snmpd: `make silent-healthcheck` prints only "OK" when the target passes.
silent-%:
	@$(MAKE) --no-print-directory $* > /dev/null && echo "OK"
