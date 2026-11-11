# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage the Prometheus exporter of the XtraDB
###################################################################################################

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

deploy: ## deploy docker-compose.yml file
	docker-compose up -d
.PHONY: deploy

restart: ## restart the exporter
	docker-compose restart
.PHONY: restart

ps: ## list the exporter container
	docker ps -a --filter name={{ xtradb_exporter_docker_container_name }}
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs

# `make silent-healthcheck` prints only OK when the healthcheck passes (used by snmpd).
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck: healthcheck-parallel ## Overall healthcheck - for parallel execution run `make --jobs 10 healthcheck`
	@echo "Everything looks: OK"
.PHONY: healthcheck

healthcheck-parallel: \
	healthcheck-container \
	healthcheck-mysql-up
.PHONY: healthcheck-parallel

healthcheck-container: ## check that the exporter container is running, and not restarting or exited
	@[ "$$(docker inspect --format {% raw %}'{{.State.Status}}'{% endraw %} {{ xtradb_exporter_docker_container_name }} 2>/dev/null)" = "running" ] || ( echo "Check exporter container: error" ; exit 1 )
	@echo "Check exporter container: OK"
.PHONY: healthcheck-container

# Asks for one collector, so it uses one MySQL connection and fits in the limit of 3 with the Prometheus scrape.
healthcheck-mysql-up: ## check that the exporter can query the XtraDB of its node
	@docker exec {{ xtradb_exporter_docker_container_name }} wget -q -T 10 -O - 'http://{{ xtradb_exporter_listen_ip | default('127.0.0.1', true) }}:{{ xtradb_exporter_listen_port }}/metrics?collect%5B%5D=global_variables' 2>/dev/null | grep -q '^mysql_up 1$$' || ( echo "Check exporter mysql_up: error" ; exit 1 )
	@echo "Check exporter mysql_up: OK"
.PHONY: healthcheck-mysql-up
