# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage {{ docker_deploy_stack_name }} in docker swarm
###################################################################################################

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

# real deploy target
_deploy: 
	docker stack deploy {{ docker_deploy_stack_name }} --compose-file docker-stack.yml
.PHONY: _deploy

deploy: | _deploy restart-services-if-need ## deploy docker stack
.PHONY: deploy

restart-services-force: ## forcelly restart all the docker stack services
	docker stack services {{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}'{% endraw %} | xargs -rt --max-lines=1 docker service update --force
.PHONY: restart

_restart-services-if-need:
	docker service ls --filter name={{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}/{{.Replicas}}'{% endraw %} | egrep -o '.*\/[0-9]+/[0-9]+' | awk -F/ '{ if ($$2 != $$3 && $$3 != 0) print $$1; exit -1 }' | xargs -rt --max-lines=1 docker service update --force
.PHONY: _restart-services-if-need

restart-services-if-need: | _restart-services-if-need status-healthcheck ## update stack services if need
.PHONY: restart-services-if-need

status-ls: ## list stack services
	docker service ls --filter name={{ docker_deploy_stack_name }}
.PHONY: status-ls

status-ps: ## list the tasks in the stack
	docker stack ps {{ docker_deploy_stack_name }}
.PHONY: status-ps

status-healthcheck-replicas: ## healthcheck - check if it's running the requested service replicas
	@docker service ls --filter name={{ docker_deploy_stack_name }} --format {% raw %}'{{.Replicas}}'{% endraw %} | egrep -o '[0-9]+/[0-9]+' | awk -F/ '{ if ($$1 != $$2 && $$2 != 0) exit -1}' && echo "OK" || echo "Not ok"
.PHONY: status-healthcheck

# List the tasks of a service
_%-ps:
	docker service ps {{ docker_deploy_stack_name }}_$*

{% for _service in docker_deploy_services %}
status-ps-{{ _service }}: _{{ _service }}-ps ## List the tasks of {{ _service }}
.PHONY: logs-{{ _service }}

{% endfor %}

# View the logs of the specified service container
_%-logs:
	docker service logs --follow --tail=500 {{ docker_deploy_stack_name }}_$*

{% for _service in docker_deploy_services %}
logs-{{ _service }}: _{{ _service }}-logs ## View last 500 lines of logs of the {{ _service }} docker service
.PHONY: logs-{{ _service }}

{% endfor %}

##################################################
# Specific openedx targets

status-mysql_1-primary: ## show primary master status on mysql_1 docker container
	@echo "Write down the value of db user '{{ openedx_mysql_containers.mysql_1.mysql_replication_login_user }}' value of 'openedx_mysql_containers.mysql_1.mysql_replication_login_password' that defaults to 'EDXAPP_MYSQL_PASSWORD_ADMIN'"
	@echo 'show master status \G' | mysql -u root --host 127.0.0.1 --port {{ openedx_mysql_containers.mysql_1.ingress_port }} -p
.PHONY: mysql-slave-status

status-mysql_2-replica: ## show replica slave status on mysql_2 docker container
	@echo "Write down the value of db user '{{ openedx_mysql_containers.mysql_2.mysql_replication_login_user }}' value of 'openedx_mysql_containers.mysql_2.mysql_replication_login_password' that defaults to 'EDXAPP_MYSQL_PASSWORD_ADMIN'"
	echo 'show slave status \G' | mysql -u root --host 127.0.0.1 --port {{ openedx_mysql_containers.mysql_2.ingress_port }} -p
.PHONY: mysql-slave-status
