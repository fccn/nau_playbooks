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
	docker ps -a --filter name=^{{ mongo_docker_container_name }}
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs

shell: ## Open shell
	@docker exec -it $$(docker ps --filter "name=$*\." -q) sh
.PHONY: shell

bash: ## Open bash on the current node for the {{ mongo_docker_container_name }} docker service
	@docker exec -it {{ mongo_docker_container_name }} bash
.PHONY: bash

mongo-shell: ## Open mongo shell
	@docker exec -it {{ mongo_docker_container_name }} mongo -u {{ mongo_docker_admin_username }} -p{{ mongo_docker_admin_password }}
.PHONY: mongo-shell

mongo-status: ## View MongoDB status
	@docker exec {{ mongo_docker_container_name }} mongo -u {{ mongo_docker_admin_username }} -p{{ mongo_docker_admin_password }} --eval "printjson(rs.status())"
.PHONY: mongo-status

healthcheck-replication: ## Check mongo replication
	@echo -n "Check mongo replication is 600 seconds (<10 minutes) seconds behind primary: "
	@(docker exec {{ mongo_docker_container_name }} mongo admin -u {{ mongo_docker_admin_username }} -p{{ mongo_docker_admin_password }} -host rs0/localhost --eval 'rs.status().members.filter(config => config.name == "{{ ansible_host }}:{{ mongo_docker_port }}")[0].state' | tail -1 | grep -q 1 ) || ( docker exec {{ mongo_docker_container_name }} mongo admin -u {{ mongo_docker_admin_username }} -p{{ mongo_docker_admin_password }} --host rs0/localhost --eval 'db.printSecondaryReplicationInfo()' | grep -A 3 "source: {{ ansible_host }}:{{ mongo_docker_port }}" | grep "behind the primary" | awk '{print $$1}' | egrep "^[0-5]?[0-9]?[0-9]$$" > /dev/null )
	@echo "OK"
.PHONY: healthcheck-replication

healthcheck-port: # Check mongo port is up
	@echo -n "Check mongo port: "
	@nc -z 127.0.0.1 {{ mongo_docker_port }}
	@echo "OK"
.PHONY: healthcheck-port

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck: ## Overall healthcheck
healthcheck: \
	healthcheck-port \
	healthcheck-replication
	@echo "Everything looks: OK"
.PHONY: healthcheck
