# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage {{ observability_docker_deploy_compose_name }} in docker swarm
###################################################################################################

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

deploy: ## deploy docker-compose.yml file
	docker-compose up -d
.PHONY: deploy

restart: ## forcelly restart all the docker compose services
	docker-compose restart
.PHONY: restart

# Restart a service
_%-restart:
	docker-compose restart $*

{% for _service in docker_deploy_services %}
restart-{{ _service }}: _{{ _service }}-restart ## Restart the {{ _service }} service
.PHONY: restart-{{ _service }}

{% endfor %}

ps: ## list containers
	docker ps -a --filter name=^{{ observability_docker_deploy_compose_name }}
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs


# View the logs of the specified service container
_%-logs:
	docker logs --timestamps --follow --tail=10 {{ observability_docker_deploy_compose_name }}_$*

{% for _service in docker_deploy_services %}
logs-{{ _service }}: _{{ _service }}-logs ## View last 10 lines of logs of the {{ _service }} docker service
.PHONY: logs-{{ _service }}

{% endfor %}

# Open bash
_%-bash:
	@docker exec -it $$(docker ps --filter "name={{ observability_docker_deploy_compose_name }}_$*\." -q) bash

{% for _service in docker_deploy_services %}
bash-{{ _service }}: _{{ _service }}-bash ## Open bash on the current node for the {{ _service }} docker service
.PHONY: bash-{{ _service }}

{% endfor %}

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck-docker-containers: ## check that docker containers are on running state
	@test $$(docker ps --filter "name={{ observability_docker_deploy_compose_name }}-*" --format {% raw %}'{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | grep "Up " | wc -l) -eq $$(docker ps --filter "name={{ observability_docker_deploy_compose_name }}-*" {% raw %}--format '{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | wc -l) || ( echo "Check docker containers status: error" ; exit 1 )
	@echo "Check docker containers status: OK"
.PHONY: healthcheck-docker-containers

healthcheck: healthcheck-parallel ## Overall healthcheck - for parallel execution run `make --jobs 10 healthcheck`
	@echo "Everything looks: OK"
.PHONY: healthcheck-parallel

#######################
# Specific
#######################

healthcheck-parallel: \
	healthcheck-docker-containers \
	healthcheck-fluentbit-forward-port
.PHONY: healthcheck-parallel

healthcheck-fluentbit-forward-port: ## check fluentbit forward port
	@nc -z -w 5 127.0.0.1 {{ observability_fluentbit_forward_port }} || ( echo "Check fluentbit forward port on {{ observability_fluentbit_forward_port }}: error" ; exit 1 )
	@echo "Check fluentbit forward port on {{ observability_fluentbit_forward_port }}: OK"
.PHONY: healthcheck-fluentbit-forward-port

{% for _metric in observability_fluentbit_metrics %}
{{ _metric | replace(".", "-") }}: ## To view the metric value execute: `make project=staticproxy service=nginx {{ _metric | replace(".", "-") }}`
# Get the value for the metric, but prevent to return a too old value.
# Get the last matched line for the project and service if the time is on the last 15 minutes, get the value, if not return zero.
	@tac {{ observability_fluentbit_data }}output-files/{{ _metric }} 2>/dev/null | grep -m1 '"$(project)","$(service)"' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$4; else print 0}'
.PHONY: {{ _metric | replace(".", "-") }}

{% endfor %}

# per second metric for total metrics that don't apply a function like average or maximum.
{% for _metric in observability_fluentbit_metrics_total %}
{{ _metric | replace(".", "-") }}-per-second: ## To view the metric value execute: `make project=staticproxy service=nginx {{ _metric | replace(".", "-") }}-per-second`
# The same has the normal
	@tac {{ observability_fluentbit_data }}output-files/{{ _metric }} 2>/dev/null | grep -m1 '"$(project)","$(service)"' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$4/300; else print 0}'
.PHONY: {{ _metric | replace(".", "-") }}-per-second

{% endfor %}

metrics-requests-last5m-code: ## To view the metric value execute: `make project=staticproxy service=nginx code=301 metrics-requests-last5m-code`
	@tac {{ observability_fluentbit_data }}/output-files/metrics.requests.last5m.code 2>/dev/null | grep -m1 '"$(project)","$(service)",$(code)' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$5; else print 0}'
.PHONY: metrics-requests-last5m-code

metrics-requests-last5m-code-per-second: ## To view the metric value execute: `make project=staticproxy service=nginx code=301 metrics-requests-last5m-code-per-second`
# The same has the normal
	@tac {{ observability_fluentbit_data }}/output-files/metrics.requests.last5m.code 2>/dev/null | grep -m1 '"$(project)","$(service)",$(code)' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$5/300; else print 0}'
.PHONY: metrics-requests-last5m-code-per-second

