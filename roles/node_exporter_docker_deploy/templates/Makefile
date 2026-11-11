# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage the Prometheus node_exporter
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
	docker ps -a --filter name={{ node_exporter_docker_container_name }}
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
	healthcheck-metrics
.PHONY: healthcheck-parallel

healthcheck-container: ## check that the exporter container is running, and not restarting or exited
	@[ "$$(docker inspect --format {% raw %}'{{.State.Status}}'{% endraw %} {{ node_exporter_docker_container_name }} 2>/dev/null)" = "running" ] || ( echo "Check exporter container: error" ; exit 1 )
	@echo "Check exporter container: OK"
.PHONY: healthcheck-container

healthcheck-metrics: ## check that the exporter answers with the metrics of the host
	@docker exec {{ node_exporter_docker_container_name }} wget -q -T 10 -O - 'http://{{ node_exporter_listen_ip | default('127.0.0.1', true) }}:{{ node_exporter_listen_port }}/metrics' 2>/dev/null | grep -q '^node_uname_info' || ( echo "Check exporter metrics: error" ; exit 1 )
	@echo "Check exporter metrics: OK"
.PHONY: healthcheck-metrics
