# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage Elastic Search
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

shell: ## Open shell
	@docker exec -it {{ elasticsearch_docker_container_name }} sh
.PHONY: shell

bash: ## Open bash on the current node for the {{ elasticsearch_docker_container_name }} docker service
	@docker exec -it {{ elasticsearch_docker_container_name }} bash
.PHONY: bash

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck-elasticsearch-port: ## Check the elasticsearch port is up
	@echo -n "Check elasticsearch port: "
	@nc -z 127.0.0.1 {{ elasticsearch_http_port }}
	@echo "OK"
.PHONY: healthcheck-elasticsearch-port

healthcheck-elasticsearch-replication: ## Check elastic search cluster replication status
	@echo -n "Check elasticsearch cluster: "
	@test $$(curl --silent 'http://localhost:{{ elasticsearch_http_port }}/_cluster/health?pretty' | grep 'number_of_nodes' | egrep -o '[0-9]+') -eq {{ elasticsearch_discovery_seed_hosts | length }}
	@test $$(curl --silent 'http://localhost:{{ elasticsearch_http_port }}/_cluster/health?level=shards&pretty' | egrep -o "status.*\," | sort | uniq | egrep -o "\"[^\ ]+\"") = "\"green\""
	@echo "OK"
.PHONY: healthcheck-elasticsearch-replication

healthcheck: ## Overall healthcheck
healthcheck: \
	healthcheck-elasticsearch-port \
	healthcheck-elasticsearch-replication
	@echo "Everything looks: OK"
.PHONY: healthcheck