# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage xtradb
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
	docker ps --filter name={{ xtradb_docker_container_name }}
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs

shell: ## Open shell
	@docker exec -it {{ xtradb_docker_container_name }} sh
.PHONY: shell

bash: ## Open bash on the current node for the {{ xtradb_docker_container_name }} docker service
	@docker exec -it {{ xtradb_docker_container_name }} bash
.PHONY: bash

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck-memory: ## check that containers doesn't use more than 90% of its available memory
	@docker stats --no-stream --format "table {% raw %}{{.Name}}\t{{.MemPerc}}{% endraw %}" | egrep "^{{ xtradb_docker_container_name }}" | awk '{print $$2}' | sed 's/%//g' | LC_NUMERIC=POSIX awk '$$0 > 90.0 {exit 1}'
.PHONY: healthcheck-memory

healthcheck: healthcheck-parallel ## Overall healthcheck - for parallel execution run `make --jobs 10 healthcheck`
	@echo "Everything looks: OK"
.PHONY: healthcheck-parallel

healthcheck-parallel: \
	healthcheck-xtradb-mysql-port \
	healthcheck-xtradb-node-ready \
	healthcheck-memory
.PHONY: healthcheck-parallel

healthcheck-xtradb-mysql-port: ## Check XtraDB MySQL port
	@nc -z -w 5 127.0.0.1 {{ xtradb_mysql_port }} || ( echo "Check xtradb mysql port: error" ; exit 1 )
	@echo "Check xtradb mysql port: OK"
.PHONY: healthcheck-xtradb-mysql-port

xtradb-showprocess-list: ## show the processes inside xtradb
	@docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --execute="show processlist;"'
.PHONY: xtradb-showprocess-list

xtradb-shell: ## open mysl shell to run SQL commands
	@docker exec -it {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }}'
.PHONY: xtradb-shell

xtradb-connections-count: ## Number of connections
	@docker exec -i {{ xtradb_docker_container_name }} bash -c 'echo "SELECT COUNT(1) FROM information_schema.PROCESSLIST;" | MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --skip-column-names'
.PHONY: xtradb-connections-count

xtradb-connections-active-count: ## Number of active connections
	@docker exec -i {{ xtradb_docker_container_name }} bash -c 'echo "SELECT COUNT(1) FROM information_schema.PROCESSLIST WHERE INFO IS NOT NULL;" | MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --skip-column-names'
.PHONY: xtradb-connections-active-count

healthcheck-xtradb-node-ready: ## Check XtraDB node is ready to accept connections
	@docker exec -i {{ xtradb_docker_container_name }} bash -c 'echo "show status like \"wsrep_ready\";" | MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --skip-column-names' | awk '{print $$2}' | grep --quiet "ON" || ( echo "Check XtraDB node is ready to accept connections: error" ; exit 1 )
	@echo "Check XtraDB node is ready to accept connections: OK"
.PHONY: xtradb-shell
