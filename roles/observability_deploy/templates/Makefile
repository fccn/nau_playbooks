# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage {{ docker_deploy_stack_name }} in docker swarm
###################################################################################################

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

deploy: ## deploy docker stack
	docker stack deploy {{ docker_deploy_stack_name }} --compose-file docker-stack.yml
.PHONY: deploy

restart-services-force: ## forcelly restart all the docker stack services
	docker stack services {{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}'{% endraw %} | xargs -rt --max-lines=1 docker service update --force
.PHONY: restart

restart-services-if-need: ## update stack services if need
	docker service ls --filter name={{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}/{{.Replicas}}'{% endraw %} | egrep -o '.*\/[0-9]+/[0-9]+' | awk -F/ '{ if ($$2 != $$3 && $$3 != 0) print $$1; }' | xargs -rt --max-lines=1 docker service update --force
.PHONY: restart-services-if-need

# Restart a service
_%-restart:
	docker service update --force {{ docker_deploy_stack_name }}_$*

{% for _service in docker_deploy_services %}
restart-{{ _service }}: _{{ _service }}-restart ## Restart the {{ _service }} service
.PHONY: restart-{{ _service }}

{% endfor %}

ls: ## List all the {{ docker_deploy_stack_name }} stack services
	docker service ls --filter name={{ docker_deploy_stack_name }}
.PHONY: ls

ps: ## list the tasks in the stack
	docker stack ps {{ docker_deploy_stack_name }}
.PHONY: ps

healthcheck-replicas: ## healthcheck - check if it's running the requested service replicas
	@echo -n 'Check docker stack replicas: '
	@docker service ls --filter name={{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}|{{.Replicas}}'{% endraw %} | egrep -v "[_-]job" | egrep -o '[0-9]+/[0-9]+' | awk -F/ '{ if ($$1 != $$2 && $$2 != 0) exit -1}'
	@echo "OK"
.PHONY: healthcheck-replicas

tasks: ## list the latest docker tasks
	@docker stack ps {{ docker_deploy_stack_name }} | grep -v " \\\\_ "
.PHONY: tasks

healthcheck-tasks: ## check if all latest docker tasks are working ok
	@echo -n 'Check docker tasks: '
	@docker stack ps {{ docker_deploy_stack_name }} | tail -n +2 | grep -v " \\\\_ " | egrep -v "[_-]job" | awk '{ if ( $$5 != $$6 ) {exit -1} }'
	@echo "OK"
.PHONY: healthcheck-tasks

# List the tasks of a service
_%-ps:
	docker service ps {{ docker_deploy_stack_name }}_$* --no-trunc

{% for _service in docker_deploy_services %}
ps-{{ _service }}: _{{ _service }}-ps ## List the tasks of {{ _service }}
.PHONY: ps-{{ _service }}

{% endfor %}

# View the logs of the specified service container
_%-logs:
	docker service logs --timestamps --follow --tail=10 {{ docker_deploy_stack_name }}_$*

{% for _service in docker_deploy_services %}
logs-{{ _service }}: _{{ _service }}-logs ## View last 10 lines of logs of the {{ _service }} docker service
.PHONY: logs-{{ _service }}

{% endfor %}

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

#######################
# Specific
#######################

healthcheck: ## Overall healthcheck
healthcheck: \
	healthcheck-replicas \
	healthcheck-tasks
	@echo "Everything looks: OK"
.PHONY: healthcheck
 
{% for _metric in observability_fluentbit_metrics %}
{{ _metric | replace(".", "-") }}: ## To view the metric value execute: `make stack=staticproxy service=nginx {{ _metric | replace(".", "-") }}`
# Get the value for the metric, but prevent to return a too old value.
# Get the last matched line for the stack and service if the time is on the last 15 minutes, get the value, if not return zero.
	@tac {{ observability_fluentbit_aggregator_data }}output-files/{{ _metric }} | grep -m1 '"$(stack)","$(service)"' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$4; else print 0}'
.PHONY: {{ _metric | replace(".", "-") }}

{% endfor %}

# per second metric for total metrics that don't apply a function like average or maximum.
{% for _metric in observability_fluentbit_metrics_total %}
{{ _metric | replace(".", "-") }}-per-second: ## To view the metric value execute: `make stack=staticproxy service=nginx {{ _metric | replace(".", "-") }}-per-second`
# The same has the normal
	@tac {{ observability_fluentbit_aggregator_data }}output-files/{{ _metric }} | grep -m1 '"$(stack)","$(service)"' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$4/300; else print 0}'
.PHONY: {{ _metric | replace(".", "-") }}-per-second

{% endfor %}


# metrics.requests.last5m.code
