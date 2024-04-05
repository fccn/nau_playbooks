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
	docker ps -a --filter name=^{{ redis_docker_container_name }}
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs

shell: ## Open shell
	@docker exec -it $$(docker ps --filter "name=$*\." -q) sh
.PHONY: shell

bash: ## Open bash on the current node for the {{ redis_docker_container_name }} docker service
	@docker exec -it $$(docker ps --filter "name={{ redis_docker_container_name }}" -q) bash
.PHONY: bash

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck-memory: ## check that containers doesn't use more than 90% of its available memory
	@docker stats --no-stream --format "table {% raw %}{{.Name}}\t{{.MemPerc}}{% endraw %}" | egrep "^{{ redis_docker_container_name }}" | awk '{print $$2}' | sed 's/%//g' | LC_NUMERIC=POSIX awk '$$0 > 90.0 {exit 1}'
.PHONY: healthcheck-memory

healthcheck-port: ## Check redis port
	@echo -n "Check redis port: "
	@nc -z -w 5 127.0.0.1 {{ redis_docker_port }}
	@echo "OK"
.PHONY: healthcheck-port

healthcheck: healthcheck-parallel ## Overall healthcheck - for parallel execution run `make --jobs 10 healthcheck`
	@echo "Everything looks: OK"
.PHONY: healthcheck-parallel

healthcheck-parallel: \
	healthcheck-port \
	healthcheck-memory
.PHONY: healthcheck-parallel
