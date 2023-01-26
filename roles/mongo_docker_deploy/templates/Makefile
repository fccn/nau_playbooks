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
	docker-compose ps
.PHONY: ps

# View the logs of the specified service container
_%-logs:
	docker-compose logs $*

# Open bash
_%-bash:
	@docker exec -it $$(docker ps --filter "name=$*\." -q) bash

# Open sh
_%-sh:
	@docker exec -it $$(docker ps --filter "name=$*\." -q) sh

bash-{{ mongo_docker_container_name }}: _{{ mongo_docker_container_name }}-bash ## Open bash on the current node for the {{ mongo_docker_container_name }} docker service
.PHONY: bash-{{ mongo_docker_container_name }}

sh-{{ mongo_docker_container_name }}: _{{ mongo_docker_container_name }}-bash ## Open sh on the current node for the {{ mongo_docker_container_name }} docker service
.PHONY: sh-{{ mongo_docker_container_name }}

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck: ## Check the mongo port is up
	@echo -n "Check mongo port: "
	@nc -z 127.0.0.1 {{ mongo_docker_published_port }}
	@echo "OK"
.PHONY: healthcheck
