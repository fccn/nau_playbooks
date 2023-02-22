# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage {{ richie_docker_deploy_compose_name }} in docker swarm
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
	docker-compose ps
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs


# View the logs of the specified service container
_%-logs:
	docker logs --timestamps --follow --tail=10 {{ richie_docker_deploy_compose_name }}-$*

{% for _service in docker_deploy_services %}
logs-{{ _service }}: _{{ _service }}-logs ## View last 10 lines of logs of the {{ _service }} docker service
.PHONY: logs-{{ _service }}

{% endfor %}

# Open bash
_%-bash:
	@test "$$(docker stack ps {{ richie_docker_deploy_compose_name }} | grep -v " \\\\_ " | grep Running | grep "$*\\." | awk '{print $$4}')" = "$(shell hostname)" || { echo "Container is not running or is running in other docker swarm node." ; exit 1; }
	@docker exec -it $$(docker ps --filter "name={{ richie_docker_deploy_compose_name }}_$*\." -q) bash

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
	@echo -n "Check docker containers status: "
	@test $$(docker ps --filter "name={{ richie_docker_deploy_compose_name }}-*" --format {% raw %}'{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | grep "Up " | wc -l) -eq $$(docker ps --filter "name={{ richie_docker_deploy_compose_name }}-*" {% raw %}--format '{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | wc -l)
	@echo "OK"
.PHONY: healthcheck-docker-containers

#######################
# Specific
#######################

healthcheck: ## Overall healthcheck
healthcheck: \
	healthcheck-mysql-port \
	healthcheck-redis-port \
	healthcheck-docker-containers \
	healthcheck-elasticsearch \
	{{ ['healthcheck-'] | product(richie_sites.keys()|list) | map('join') | product(['_app_job']) | map('join') | join(' \\\n\t') }}
	@echo "Everything looks: OK"
.PHONY: healthcheck


#######################
# MySQL 
#######################

{% for _site, config in richie_sites.items() %}
BACKUP_FILE_{{ _site }} ?= richie-{{ _site }}-mysql-db-backup.sql.gz
backup-mysql-{{ _site }}: ## backup mysql db of {{ _site }} site
	@echo -n "Backing up MySQL database of '{{ _site }}'... "
	@rm -f ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})
	@MYSQL_PWD="{{ richie_MYSQL_ROOT_PASSWORD}}" /usr/bin/mysqldump -u root --host {{ richie_docker_deploy_mysql_host }} --port {{ richie_docker_deploy_mysql_port }} --single-transaction {{ config.app_environment_variables.DB_NAME }} | gzip -c -9  > ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})
	@echo 'Done! File: $(BACKUP_FILE_{{ _site }})'
.PHONY: backup-mysql-{{ _site }}

_restore-mysql-{{ _site }}-change-environment:
	@test -n "${FROM_ENV}" || ( echo "Missing argument 'FROM_ENV', FROM_ENV='www.example.com'" && exit 1)
	@test -n "${TO_ENV}"   || ( echo "Missing argument 'TO_ENV', FROM_ENV='dev.example.com'"   && exit 1)
	@cat ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }}) | gzip -d > ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})_temp
	@sed -in "s/${FROM_ENV}/${TO_ENV}/g" ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})_temp
	@cat ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})_temp | gzip -c -9  > ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})
	@rm ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})_temp
	@echo "Successfully change the mysql backup from '${FROM_ENV}' to '${TO_ENV}'."
.PHONY: _restore-mysql-{{ _site }}-change-environment

restore-mysql-{{ _site }}-change-environment: | _restore-mysql-{{ _site }}-change-environment restore-mysql-{{ _site }} ## restore mysql db of {{ _site }} from a different environment, use: make restore-mysql-{{ _site }}-change-environment FROM_ENV="nau.edu.pt" TO_ENV="stage.nau.fccn.pt"
.PHONY: restore-mysql-{{ _site }}-change-environment

restore-mysql-{{ _site }}: ## restore mysql db of {{ _site }} site
	@echo -n "Loading to '{{ config.app_environment_variables.DB_NAME }}' MySQL database the backfile '$(BACKUP_FILE_{{ _site }})'. You can monitor the progress running 'make mysql_1-showprocess-list'."
	@cat ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }}) | gzip -d | MYSQL_PWD="{{ richie_MYSQL_ROOT_PASSWORD }}" /usr/bin/mysql -u root --host {{ richie_docker_deploy_mysql_host }} --port {{ richie_docker_deploy_mysql_port }} {{ config.app_environment_variables.DB_NAME }}
	@echo 'Done!'
.PHONY: restore-mysql-{{ _site }}

{% endfor %}

healthcheck-mysql-port: ## check mysql port
	@echo -n "Check mysql port for {{ richie_docker_deploy_mysql_host }}:{{ richie_docker_deploy_mysql_port }} "
	@nc -z {{ richie_docker_deploy_mysql_host }} {{ richie_docker_deploy_mysql_port }}
	@echo "OK"
.PHONY: healthcheck-mysql-port

#######################
# Elasticsearch
#######################

healthcheck-elasticsearch: ## Run elastic search healthcheck cluster
	@echo -n "Check elasticsearch cluster: "
	@test $$(curl --silent '{{ richie_docker_deploy_elasticsearch_cluster_hosts_url[0] }}/_cluster/health?pretty' | grep 'number_of_nodes' | egrep -o '[0-9]+') -eq {{ richie_docker_deploy_elasticsearch_cluster_hosts_url | length }}
	@test $$(curl --silent '{{ richie_docker_deploy_elasticsearch_cluster_hosts_url[0] }}/_cluster/health?level=shards&pretty' | egrep -o "status.*\," | sort | uniq | egrep -o "\"[^\ ]+\"") = "\"green\""
{% for es in richie_docker_deploy_elasticsearch_cluster_hosts_url %}
	@test $$(curl -sLI {{ es }} -o /dev/null -w '%{http_code}\n') -eq 200
{% endfor %}
	@echo "OK"
.PHONY: healthcheck-elasticsearch

#######################
# Redis
#######################

healthcheck-redis-port: ## check load balancer HAProxy redis port
	@echo -n "Check load balancer HAProxy elasticsearch port: "
	@nc -z {{ richie_docker_deploy_redis_host }} {{ richie_docker_deploy_redis_port }}
	@echo "OK"
.PHONY: healthcheck-redis-port

########################
# App job
########################

{% for _site, config in richie_sites.items() %}
# check if last job run has finished with complete stateand without any error
healthcheck-{{ _site }}_app_job: ## check if the migrate and bootstrap_elasticsearch django commands have finished with success for {{ _site }} site
	@echo -n "Check {{ _site }}_app_job with django migrate and bootstrap elasticsearch commands: "
	@test $$(docker ps --filter "name={{ richie_docker_deploy_compose_name }}_{{ _site }}_app_job" -a | grep "Exited (0)" | wc -l) -eq 1
	@echo "OK"
.PHONY: healthcheck-{{ _site }}_app_job

{% endfor %}