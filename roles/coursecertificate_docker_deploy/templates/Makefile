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

healthcheck-docker-containers: ## check that docker containers are on running state
	@echo -n "Check docker containers status: "
	@test $$(docker ps --filter "name={{ coursecertificate_docker_deploy_compose_name }}-*" --format {% raw %}'{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | grep "Up " | wc -l) -eq $$(docker ps --filter "name={{ coursecertificate_docker_deploy_compose_name }}-*" {% raw %}--format '{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | wc -l)
	@echo "OK"
.PHONY: healthcheck-docker-containers


#######################
# Specific
#######################

healthcheck: ## Overall healthcheck
healthcheck: \
	healthcheck-docker-containers \
	healthcheck-nginx-ports
	@echo "Everything looks: OK"
.PHONY: healthcheck

healthcheck-nginx-ports: ## check nginx ports
	@echo -n "Check nginx ports: "
	@nc -z 127.0.0.1 {{ coursecertificate_nginx_http_ingress_port }}
	@nc -z 127.0.0.1 {{ coursecertificate_nginx_https_ingress_port }}
	@echo "OK"
.PHONY: healthcheck-nginx-ports
