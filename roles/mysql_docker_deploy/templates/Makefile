# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage mysql
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
	docker ps --filter name={{ mysql_docker_container_name }}
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs

shell: ## Open shell
	@docker exec -it {{ mysql_docker_container_name }} sh
.PHONY: shell

bash: ## Open bash on the current node for the {{ mysql_docker_container_name }} docker service
	@docker exec -it {{ mysql_docker_container_name }} bash
.PHONY: bash

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck-memory: ## check that containers doesn't use more than 90% of its available memory
	@docker stats --no-stream --format "table {% raw %}{{.Name}}\t{{.MemPerc}}{% endraw %}" | egrep "^{{ mysql_docker_container_name }}" | awk '{print $$2}' | sed 's/%//g' | LC_NUMERIC=POSIX awk '$$0 > 90.0 {exit 1}'
.PHONY: healthcheck-memory

healthcheck: healthcheck-parallel ## Overall healthcheck - for parallel execution run `make --jobs 10 healthcheck`
	@echo "Everything looks: OK"
.PHONY: healthcheck-parallel

healthcheck-parallel: \
	healthcheck-mysql-port \
{% if mysql_docker_primary %}
	healthcheck-mysql-primary \
{% else %}
	healthcheck-mysql-replica \
{% endif %}
	healthcheck-memory
.PHONY: healthcheck-parallel

healthcheck-mysql-port: ## check mysql port
	@echo -n "Check mysql port for {{ mysql_docker_container_name }}: "
	@nc -z -w 5 127.0.0.1 {{ mysql_docker_port }}
	@echo "OK"
.PHONY: healthcheck-mysql-port

{% if mysql_docker_primary %}
healthcheck-mysql-primary: ## show primary master status
	@echo -n "Check mysql master status: "
	@echo 'show master status \G' | MYSQL_PWD="{{ mysql_health_check_pass }}" mysql -u {{ mysql_health_check_user }} --host 127.0.0.1 --port {{ mysql_docker_port }} > /dev/null
	@echo "OK"
.PHONY: healthcheck-mysql-primary

{% endif %}
mysql-showprocess-list: ## show the processes inside mysql
	@MYSQL_PWD="{{ mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ mysql_docker_port }} --execute="show processlist;"
.PHONY: mysql-showprocess-list

mysql-shell: ## open mysl shell to run SQL commands
	@MYSQL_PWD="{{ mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ mysql_docker_port }}
.PHONY: mysql-shell

mysql-connections-count: ## Number of connections
	@echo 'SELECT COUNT(1) FROM information_schema.PROCESSLIST;' | MYSQL_PWD="" mysql -u {{ mysql_health_check_user }} --host 127.0.0.1 --port {{ mysql_docker_port }} --skip-column-names
.PHONY: mysql-connections-count

mysql-connections-active-count: ## Number of active connections
	@echo 'SELECT COUNT(1) FROM information_schema.PROCESSLIST WHERE INFO IS NOT NULL;' | MYSQL_PWD="" mysql -u {{ mysql_health_check_user }} --host 127.0.0.1 --port {{ mysql_docker_port }} --skip-column-names
.PHONY: mysql-connections-active-count

{% if not mysql_docker_primary %}
healthcheck-mysql-replica: ## show replica slave status
	@echo -n "Check mysql replica {{ mysql_docker_container_name }} seconds behind primary is lower than 600 seconds (< 10 minutes): "
	@echo 'show slave status \G' | MYSQL_PWD="{{ mysql_health_check_pass }}" mysql -u {{ mysql_health_check_user }} --host 127.0.0.1 --port {{ mysql_docker_port }} | egrep "Seconds_Behind_Master: [0-5]?[0-9]?[0-9]$$" > /dev/null
	@echo "OK"
.PHONY: healthcheck-mysql-replica

mysql-replica-seconds-behind: ## show how much seconds the replica in behind the primary should be lower than 600 seconds == ( < 10 minutes )
	@echo 'show slave status \G' | MYSQL_PWD="{{ mysql_health_check_pass }}" mysql -u {{ mysql_health_check_user }} --host 127.0.0.1 --port {{ mysql_docker_port }} | egrep -o "Seconds_Behind_Master: [0-9]+$$" | egrep -o "[0-9]+"
.PHONY: mysql-replica-seconds-behind

mysql-replica-status: ## show the status of the replica
	@echo 'show slave status \G' | MYSQL_PWD="{{ mysql_health_check_pass }}" mysql -u {{ mysql_health_check_user }} --host 127.0.0.1 --port {{ mysql_docker_port }}
.PHONY: mysql-replica-status

{% endif %}
