# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage {{ docker_deploy_stack_name }} in docker swarm
###################################################################################################

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

# real deploy target
_deploy: 
	docker stack deploy {{ docker_deploy_stack_name }} --compose-file docker-stack.yml
.PHONY: _deploy

deploy: | _deploy restart-services-if-need ## deploy docker stack
.PHONY: deploy

restart-services-force: ## forcelly restart all the docker stack services
	docker stack services {{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}'{% endraw %} | xargs -rt --max-lines=1 docker service update --force
.PHONY: restart

_restart-services-if-need:
	docker service ls --filter name={{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}/{{.Replicas}}'{% endraw %} | egrep -o '.*\/[0-9]+/[0-9]+' | awk -F/ '{ if ($$2 != $$3 && $$3 != 0) print $$1; exit -1 }' | xargs -rt --max-lines=1 docker service update --force
.PHONY: _restart-services-if-need

restart-services-if-need: | _restart-services-if-need status-healthcheck ## update stack services if need
.PHONY: restart-services-if-need

status-ls: ## list stack services
	docker service ls --filter name={{ docker_deploy_stack_name }}
.PHONY: status-ls

status-ps: ## list the tasks in the stack
	docker stack ps {{ docker_deploy_stack_name }}
.PHONY: status-ps

status-healthcheck-replicas: ## healthcheck - check if it's running the requested service replicas
	@echo -n 'Check docker stack replicas: '
	@docker service ls --filter name={{ docker_deploy_stack_name }} --format {% raw %}'{{.Replicas}}'{% endraw %} | egrep -o '[0-9]+/[0-9]+' | awk -F/ '{ if ($$1 != $$2 && $$2 != 0) exit -1}'
	@echo "OK"
.PHONY: status-healthcheck-replicas

# List the tasks of a service
_%-ps:
	docker service ps {{ docker_deploy_stack_name }}_$*

{% for _service in docker_deploy_services %}
status-ps-{{ _service }}: _{{ _service }}-ps ## List the tasks of {{ _service }}
.PHONY: logs-{{ _service }}

{% endfor %}

# View the logs of the specified service container
_%-logs:
	docker service logs --follow --tail=500 {{ docker_deploy_stack_name }}_$*

{% for _service in docker_deploy_services %}
logs-{{ _service }}: _{{ _service }}-logs ## View last 500 lines of logs of the {{ _service }} docker service
.PHONY: logs-{{ _service }}

{% endfor %}

#######################
# Specific
#######################

status-healthcheck: | {{ ['status-healthcheck-mysql-port-'] | product(openedx_mysql_containers.keys()|list) | map('join') | join(' ') }} status-healthcheck-elasticsearch status-healthcheck-load-balancer-haproxy-statistics-port status-healthcheck-load-balancer-haproxy-elasticsearch-port status-healthcheck-replicas ## Overall healthcheck
	@echo "Everything looks: OK"
.PHONY: status-healthcheck

restart-redis_sentinel:
{% for container, config in openedx_redis_sentinel_containers.items() %}
	@echo "Restarting container {{ openedx_docker_deploy_stack_name }}_{{ container }}"
	docker service update --force {{ openedx_docker_deploy_stack_name }}_{{ container }}
{% endfor %}
.PHONY: restart-redis_sentinel

#######################
# MySQL
#######################

status-mysql-primary: ## show primary master status on mysql_1 docker container
	@echo "Write down the value of db user '{{ openedx_mysql_containers.mysql_1.mysql_replication_login_user }}' value of 'openedx_mysql_containers.mysql_1.mysql_replication_login_password'"
	@echo 'show master status \G' | mysql -u root --host 127.0.0.1 --port {{ openedx_mysql_primary.ingress_port }} -p
.PHONY: status-mysql-primary

{% for container, config in openedx_mysql_containers.items() %}
{% if not config.primary %}
status-mysql-replica-{{ container }}: ## show replica slave status on {{ container }} docker container
	@echo "Write down the value of db user '{{ config.mysql_replication_login_user }}' value of 'openedx_mysql_containers.{{ container }}.mysql_replication_login_password'"
	echo 'show slave status \G' | mysql -u root --host 127.0.0.1 --port {{ config.ingress_port }} -p
.PHONY: status-mysql-replica-{{ container }}

{% endif %}
{% endfor %}
{% for container, config in openedx_mysql_containers.items() %}
status-healthcheck-mysql-port-{{ container }}: ## check mysql port for {{ container }}
	@echo -n "Check mysql port for {{ container }}: "
	@nc -z 127.0.0.1 {{ config.ingress_port }}
	@echo "OK"
.PHONY: status-healthcheck-port-{{ container }}
{% endfor %}

#######################
# Elasticsearch
#######################

{% for container, config in openedx_elasticsearch_containers.items() %}
status-healthcheck-{{ container }}: ## Run elasticsearch healthcheck cluster on {{ openedx_docker_deploy_stack_name }}_{{ container }} container
	@echo -n "Check Elasticsearch {{ container }}: "
	@test $$(docker exec -u root -it $$(docker ps -q -f name={{ openedx_docker_deploy_stack_name }}_{{ container }}) curl -X GET '127.0.0.1:9200/_cluster/health?pretty' | grep 'number_of_nodes' | egrep -o '[0-9]+') -eq {{ openedx_elasticsearch_containers.keys() | length }}
	@test $$(docker exec -u root -it $$(docker ps -q -f name={{ openedx_docker_deploy_stack_name }}_{{ container }}) curl -X GET '127.0.0.1:9200/_cluster/health?level=shards&pretty' | egrep -o "status.*\," | sort | uniq | egrep -o "\"[^\ ]+\"") = "\"green\""
	@echo "OK"
.PHONY: status-healthcheck-{{ container }}

{% endfor %}

status-healthcheck-elasticsearch: ## Run elastic search healthcheck cluster using load balancer
	@echo -n "Check Elasticsearch cluster: "
	@test $$(curl -s 'http://localhost:{{ openedx_load_balancer_haproxy_elasticsearch_port }}/_cluster/health?pretty' | grep 'number_of_nodes' | egrep -o '[0-9]+') -eq {{ openedx_elasticsearch_containers.keys() | length }}
	@test $$(curl -s 'http://localhost:{{ openedx_load_balancer_haproxy_elasticsearch_port }}/_cluster/health?level=shards&pretty' | egrep -o "status.*\," | sort | uniq | egrep -o "\"[^\ ]+\"") = "\"green\""
	@echo "OK"
.PHONY: status-healthcheck-elasticsearch

#######################
# HAProxy
#######################

status-healthcheck-load-balancer-haproxy-statistics-port: ## check load balancer HAProxy statistics {{ openedx_load_balancer_haproxy_statistics_port }} port
	@echo -n "Check load balancer HAProxy statistics port: "
	@nc -z 127.0.0.1 {{ openedx_load_balancer_haproxy_statistics_port }}
	@echo "OK"
.PHONY: status-healthcheck-load-balancer-haproxy-statistics-port

status-healthcheck-load-balancer-haproxy-elasticsearch-port: ## check load balancer HAProxy elasticsearch {{ openedx_load_balancer_haproxy_elasticsearch_port }} port
	@echo -n "Check load balancer HAProxy elasticsearch port: "
	@nc -z 127.0.0.1 {{ openedx_load_balancer_haproxy_elasticsearch_port }}
	@echo "OK"
.PHONY: status-healthcheck-load-balancer-haproxy-elasticsearch-port
