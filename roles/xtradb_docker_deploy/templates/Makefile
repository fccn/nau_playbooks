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
	healthcheck-xtradb-wsrep-cluster-status \
	healthcheck-xtradb-wsrep-connected \
	healthcheck-xtradb-wsrep-ready \
	healthcheck-xtradb-mysql-port \
	healthcheck-xtradb-node-ready \
	healthcheck-memory
.PHONY: healthcheck-parallel

healthcheck-xtradb-mysql-port: ## Check XtraDB MySQL port
	@nc -z -w 5 127.0.0.1 {{ xtradb_mysql_port }} >/dev/null 2>&1 || ( echo "Check xtradb mysql port: error" ; exit 1 )
	@echo "Check xtradb mysql port: OK"
.PHONY: healthcheck-xtradb-mysql-port

healthcheck-xtradb-wsrep-cluster-status:
	@docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --execute="show status like \"wsrep_cluster_status\";"' | grep -q Primary || ( echo "Check xtradb wsrep cluster status: error" ; exit 1 )
	@echo "Check xtradb wsrep cluster status: OK"
.PHONY: healthcheck-xtradb-wsrep-cluster-status

healthcheck-xtradb-wsrep-connected:
	@docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --execute="show status like \"wsrep_connected\";"' | grep -q ON || ( echo "Check xtradb wsrep connected: error" ; exit 1 )
	@echo "Check xtradb wsrep connected: OK"
.PHONY: healthcheck-xtradb-wsrep-connected

healthcheck-xtradb-wsrep-ready:
	@docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --execute="show status like \"wsrep_ready\";"' | grep -q ON || ( echo "Check xtradb wsrep ready: error" ; exit 1 )
	@echo "Check xtradb wsrep ready: OK"
.PHONY: healthcheck-xtradb-wsrep-ready

xtradb-showprocess-list: ## show the processes inside xtradb
	@docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --execute="show processlist;"'
.PHONY: xtradb-showprocess-list

xtradb-status: ## show mysql status
	@docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --execute="show status;"'
.PHONY: xtradb-status

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

xtradb-dump: ## Dump the designated databases to a file - `make xtradb-dump DATABASES="database_names" FILE=output_file.sql.gz`
	@if [ -z "$(FILE)" ]; then echo "Error: FILE parameter is required. Usage: make xtradb-dump DATABASES=\"database_names\" FILE=output_file.sql.gz"; exit 1; fi
	$(eval DB_OPTION := $(if $(DATABASES),$(DATABASES),--all-databases))
	@docker exec -it {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysqldump -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} $(DB_OPTION) --single-transaction --skip-extended-insert' | nice -n 10 gzip -c | ionice -c2 -n 7 tee $(FILE) > /dev/null
	@echo "Databases dumped to $(FILE)"
.PHONY: xtradb-dump