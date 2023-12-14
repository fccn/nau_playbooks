# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage Mongo
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
	docker ps -a --filter name=^{{ financial_manager_docker_deploy_compose_name }}
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs

shell: ## Open shell
	@docker exec -it $$(docker ps --filter "name=$*\." -q) sh
.PHONY: shell

bash: ## Open bash on the current node for the {{ financial_manager_docker_container_name_app }} docker service
	@docker exec -it $$(docker ps --filter "name={{ financial_manager_docker_container_name_app }}" -q) bash
.PHONY: bash

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck-memory: ## check that containers doesn't use more than 90% of its available memory
	@docker stats --no-stream --format "table {% raw %}{{.Name}}\t{{.MemPerc}}{% endraw %}" | egrep "^{{ financial_manager_docker_container_name_app }}" | awk '{print $$2}' | sed 's/%//g' | LC_NUMERIC=POSIX awk '$$0 > 90.0 {exit 1}'
.PHONY: healthcheck-memory

healthcheck-app-port: ## Check financial manager app port
	@echo -n "Check financial_manager port: "
	@nc -z 127.0.0.1 {{ financial_manager_app_docker_port }}
	@echo "OK"
.PHONY: healthcheck-app-port

healthcheck-docker-containers: ## check that docker containers are on running state
	@test $$(docker ps --filter "name={{ financial_manager_docker_deploy_compose_name }}-*" --format {% raw %}'{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | grep "Up " | wc -l) -eq $$(docker ps --filter "name={{ financial_manager_docker_deploy_compose_name }}-*" {% raw %}--format '{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | wc -l) || ( echo "Check docker containers status: error" ; exit 1 )
	@echo "Check docker containers status: OK"
.PHONY: healthcheck-docker-containers

healthcheck: healthcheck-parallel ## Overall healthcheck - for parallel execution run `make --jobs 10 healthcheck`
	@echo "Everything looks: OK"
.PHONY: healthcheck-parallel

healthcheck-nginx-ports: ## check nginx ports
	@nc -z 127.0.0.1 {{ financial_manager_nginx_http_ingress_port }}  || ( echo "Check nginx http port {{ financial_manager_nginx_http_ingress_port }}: error not available!" ; exit 1 )
	@nc -z 127.0.0.1 {{ financial_manager_nginx_https_ingress_port }} || ( echo "Check nginx https port {{ financial_manager_nginx_https_ingress_port }}: error not available!" ; exit 1 )
	@echo "Check nginx ports: OK"
.PHONY: healthcheck-nginx-ports

healthcheck-parallel: \
	healthcheck-mysql-port \
	healthcheck-django-cache-redis-port \
	healthcheck-celery-broker-redis-port \
	healthcheck-docker-containers \
	healthcheck-app-port \
	healthcheck-nginx-ports \
	healthcheck-memory
.PHONY: healthcheck-parallel

#######################
# Redis
#######################
healthcheck-django-cache-redis-port: ## check django cache redis port
	@nc -z {{ financial_manager_caches_default_redis_host }} {{ financial_manager_caches_default_redis_port }} || ( echo "Check django cachew redis port: error" ; exit 1; )
	@echo "Check redis port: OK"
.PHONY: healthcheck-redis-port

healthcheck-celery-broker-redis-port: ## check celery broker redis port
	@nc -z {{ financial_manager_celery_broker_redis_host }} {{ financial_manager_celery_broker_redis_port }} || ( echo "Check celery broker redis port: error" ; exit 1; )
	@echo "Check redis port: OK"
.PHONY: healthcheck-redis-port

#######################
# MySQL
#######################
healthcheck-mysql-port: ## check mysql port
	@mysqladmin ping --silent --host {{ financial_manager_mysql_docker_hostname }} --user {{ financial_manager_mysql_health_check_user }} --port {{ financial_manager_mysql_docker_port }} || ( echo "Check mysql port {{ financial_manager_mysql_docker_hostname }}:{{ financial_manager_mysql_docker_port }}: error" ; exit 1 )
	@echo "Check mysql port {{ financial_manager_mysql_docker_hostname }}:{{ financial_manager_mysql_docker_port }}: OK"
.PHONY: healthcheck-mysql-port
