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

status-healthcheck: ## healthcheck - check if it's running the requested service replicas
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
logs-{{ _service }}: _{{ _service }}-logs ## View {{ _service }} docker service logs (last 500 lines and following)
.PHONY: logs-{{ _service }}

{% endfor %}

#######################
## Specific
#

{% for _site, config in richie_sites.items() %}
BACKUP_FILE_{{ _site }} ?= richie-{{ _site }}-mysql-db-backup.sql.gz
backup-mysql-{{ _site }}: ## backup mysql db of {{ _site }} site
	@echo 'Backing up MySQL database of {{ _site }}'
	@rm -f ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})
	@MYSQL_PWD="{{ config.app_richie_MYSQL_PASSWORD}}" /usr/bin/mysqldump -u {{ config.app_richie_MYSQL_USER }} --host 127.0.0.1 --port {{ richie_mysql_primary.ingress_port }} --single-transaction {{ config.app_richie_MYSQL_DATABASE }} | gzip -c -9  > ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})
	@echo 'Done! File: $(BACKUP_FILE_{{ _site }})'
.PHONY: backup-mysql-{{ _site }}

restore-mysql-{{ _site }}: ## restore mysql db of {{ _site }} site
	@echo 'Loading to {{ config.app_richie_MYSQL_DATABASE }} MySQL database the backfile $(BACKUP_FILE_{{ _site }})'
	@cat ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }}) | gzip -d | MYSQL_PWD="{{ config.app_richie_MYSQL_PASSWORD }}" /usr/bin/mysql -u {{ config.app_richie_MYSQL_USER }} --host 127.0.0.1 --port {{ richie_mysql_primary.ingress_port }} {{ config.app_richie_MYSQL_DATABASE }}
	@echo 'Done!'
.PHONY: restore-mysql-{{ _site }}

{% endfor %}