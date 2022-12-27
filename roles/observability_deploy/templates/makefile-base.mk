
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

# Open bash
_%-bash:
	@test "$$(docker stack ps {{ docker_deploy_stack_name }} | grep -v " \\\\_ " | grep Running | grep "$*\\." | awk '{print $$4}')" = "$(shell hostname)" || { echo "Container is not running or is running in other docker swarm node." ; exit 1; }
	@docker exec -it $$(docker ps --filter "name={{ docker_deploy_stack_name }}_$*\." -q) bash

{% for _service in docker_deploy_services %}
bash-{{ _service }}: _{{ _service }}-bash ## Open bash on the current node for the {{ _service }} docker service
.PHONY: bash-{{ _service }}

{% endfor %}

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"
