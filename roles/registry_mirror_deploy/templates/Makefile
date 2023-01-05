# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage registry mirror docker service
###################################################################################################

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

deploy: ## deploy docker compose
	@docker-compose up -d
.PHONY: deploy

ps: ## list the tasks in the stack
	@docker ps --filter name={{ registry_mirror_docker_compose_name }}
.PHONY: ps

tasks: ## list the latest docker tasks
	@docker ps --filter name={{ registry_mirror_docker_compose_name }} | grep -v " \\\\_ "
.PHONY: tasks

logs: ## view registry logs
	@docker logs {{ registry_mirror_docker_compose_name }}-registry-1 -f
.PHONY: logs

bash: ## open bash on registry container
	docker exec -it $$(docker ps --filter "name={{ registry_mirror_docker_compose_name }}-registry-1" -q) bash
.PHONY: bash

healthcheck: ## Check the health of the registry service
	@echo -n "Check port: "
	@nc -z 127.0.0.1 {{ registry_mirror_port }}
	@echo "OK"
.PHONY: healthcheck
