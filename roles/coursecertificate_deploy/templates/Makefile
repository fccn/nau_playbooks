# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage {{ docker_deploy_stack_name }} in docker swarm
###################################################################################################

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

# -- Rules
default: help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

deploy: ## deploy docker stack
	docker stack deploy {{ docker_deploy_stack_name }} --compose-file docker-stack.yml
.PHONY: deploy

status-service-ls: ## list {{ docker_deploy_stack_name }} stack services
	docker service ls --filter name={{ docker_deploy_stack_name }}
.PHONY: service-ls

status-stack-ps: ## list the tasks in the {{ docker_deploy_stack_name }} stack
	docker stack ps {{ docker_deploy_stack_name }}
.PHONY: stack-ps

status-healthcheck: ## healthcheck - check if it's running the requested service replicas
	@docker service ls --filter name={{ docker_deploy_stack_name }} --format {% raw %}'{{.Replicas}}'{% endraw %} | egrep -o '[0-9]+/[0-9]+' | awk -F/ '{ if ($$1 != $$2 && $$2 != 0) exit -1}' && echo "OK" || echo "Not ok"
.PHONY: healthcheck

# View the logs of the specified service container
_%-logs:
	docker service logs --follow --tail=500 openedx_$*

{% for _service in ( (docker_deploy_templates + docker_deploy_files) | selectattr('service', 'defined') | map(attribute='service') | unique | list ) %}
logs-{{ _service }}: _{{ _service }}-logs ## View last 500 lines of logs of the {{ _service }} docker service
.PHONY: {{ _service }}-logs

{% endfor %}
