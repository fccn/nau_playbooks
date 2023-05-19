# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage {{ coursecertificate_docker_deploy_compose_name }} in docker swarm
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
	docker ps -a --filter name=^{{ coursecertificate_docker_deploy_compose_name }}
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs


# View the logs of the specified service container
_%-logs:
	docker logs --timestamps --follow --tail=10 {{ coursecertificate_docker_deploy_compose_name }}_$*

{% for _service in docker_deploy_services %}
logs-{{ _service }}: _{{ _service }}-logs ## View last 10 lines of logs of the {{ _service }} docker service
.PHONY: logs-{{ _service }}

{% endfor %}

# Open bash
_%-bash:
	@docker exec -it $$(docker ps --filter "name={{ coursecertificate_docker_deploy_compose_name }}_$*\." -q) bash

{% for _service in docker_deploy_services %}
bash-{{ _service }}: _{{ _service }}-bash ## Open bash on the current node for the {{ _service }} docker service
.PHONY: bash-{{ _service }}

{% endfor %}

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck-memory: ## check that containers doesn't use more than 90% of its available memory
	@docker stats --no-stream --format "table {% raw %}{{.Name}}\t{{.MemPerc}}{% endraw %}" | egrep "^{{ coursecertificate_docker_deploy_compose_name }}" | awk '{print $$2}' | sed 's/%//g' | LC_NUMERIC=POSIX awk '$$0 > 90.0 {exit 1}'
.PHONY: healthcheck-memory

healthcheck-docker-containers: ## check that docker containers are on running state
	@test $$(docker ps --filter "name={{ coursecertificate_docker_deploy_compose_name }}-*" --format {% raw %}'{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | grep "Up " | wc -l) -eq $$(docker ps --filter "name={{ coursecertificate_docker_deploy_compose_name }}-*" {% raw %}--format '{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | wc -l) || ( echo "Check docker containers status: error" ; exit 1 )
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
	healthcheck-nginx-ports \
	healthcheck-memory
.PHONY: healthcheck-parallel

healthcheck-nginx-ports: ## check nginx ports
	@nc -z 127.0.0.1 {{ coursecertificate_nginx_http_ingress_port }}  || ( echo "Check nginx http port {{ coursecertificate_nginx_http_ingress_port }}: error not available!" ; exit 1 )
	@nc -z 127.0.0.1 {{ coursecertificate_nginx_https_ingress_port }} || ( echo "Check nginx https port {{ coursecertificate_nginx_https_ingress_port }}: error not available!" ; exit 1 )
	@echo "Check nginx ports: OK"
.PHONY: healthcheck-nginx-ports
