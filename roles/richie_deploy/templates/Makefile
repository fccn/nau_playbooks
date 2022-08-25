# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage {{ docker_deploy_stack_name }} in docker swarm
###################################################################################################

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

deploy: ## deploy docker stack
	docker stack deploy {{ docker_deploy_stack_name }} --compose-file docker-stack.yml
.PHONY: deploy

restart-services-force: ## forcelly restart all the docker stack services
	docker stack services {{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}'{% endraw %} | xargs -rt --max-lines=1 docker service update --force
.PHONY: restart

restart-services-if-need: ## update stack services if need
	docker service ls --filter name={{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}/{{.Replicas}}'{% endraw %} | egrep -o '.*\/[0-9]+/[0-9]+' | awk -F/ '{ if ($$2 != $$3 && $$3 != 0) print $$1; }' | xargs -rt --max-lines=1 docker service update --force
.PHONY: restart-services-if-need

# Restart a service
_%-restart:
	docker service update --force {{ docker_deploy_stack_name }}_$*

{% for _service in docker_deploy_services %}
restart-{{ _service }}: _{{ _service }}-restart ## Restart the {{ _service }} service
.PHONY: restart-{{ _service }}

{% endfor %}

ls: ## List all the {{ docker_deploy_stack_name }} stack services
	docker service ls --filter name={{ docker_deploy_stack_name }}
.PHONY: ls

ps: ## list the tasks in the stack
	docker stack ps {{ docker_deploy_stack_name }}
.PHONY: ps

healthcheck-replicas: ## healthcheck - check if it's running the requested service replicas
	@echo -n 'Check docker stack replicas: '
	@docker service ls --filter name={{ docker_deploy_stack_name }} --format {% raw %}'{{.Name}}|{{.Replicas}}'{% endraw %} | grep -v _job | egrep -o '[0-9]+/[0-9]+' | awk -F/ '{ if ($$1 != $$2 && $$2 != 0) exit -1}'
	@echo "OK"
.PHONY: healthcheck-replicas

# List the tasks of a service
_%-ps:
	docker service ps {{ docker_deploy_stack_name }}_$* --no-trunc

{% for _service in docker_deploy_services %}
ps-{{ _service }}: _{{ _service }}-ps ## List the tasks of {{ _service }}
.PHONY: logs-{{ _service }}

{% endfor %}

# View the logs of the specified service container
_%-logs:
	docker service logs --follow --tail=500 {{ docker_deploy_stack_name }}_$*

{% for _service in docker_deploy_services %}
logs-{{ _service }}: _{{ _service }}-logs ## View last 500 lines of logs of the {{ _service }} docker service
.PHONY: logs-{{ _service }}

{% endfor %}

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"


#######################
# Specific
#######################

healthcheck: ## Overall healthcheck
healthcheck: \
	healthcheck-replicas \
	healthcheck-load-balancer-haproxy-statistics-port \
	{{ ['healthcheck-mysql-port-'] | product(richie_mysql_containers.keys()|list) | map('join') | join(' \\\n\t') }} \
	healthcheck-elasticsearch \
	healthcheck-load-balancer-haproxy-elasticsearch-port \
	healthcheck-load-balancer-haproxy-redis-port \
	healthcheck-mysql-primary \
{% for container, config in richie_mysql_containers.items() %}
{% if not config.primary %}
	healthcheck-mysql-replica-{{ container }} \
{% endif %}
{% endfor %}
	{{ ['healthcheck-'] | product(richie_sites.keys()|list) | map('join') | product(['_app_job']) | map('join') | join(' \\\n\t') }}
	@echo "Everything looks: OK"
.PHONY: healthcheck


#######################
# MySQL 
#######################

healthcheck-mysql-primary: ## show primary master status on mysql_1 docker container
	@echo -n "Check mysql master status: "
	@echo 'show master status \G' | MYSQL_PWD="{{ openark_orchestrator_client_password }}" mysql -u {{ openark_orchestrator_client_user }} --host 127.0.0.1 --port {{ richie_mysql_primary.ingress_port }} > /dev/null
	@echo "OK"
.PHONY: healthcheck-mysql-primary

{% for container, config in richie_mysql_containers.items() %}
{% if not config.primary %}
healthcheck-mysql-replica-{{ container }}: ## show replica slave status on {{ container }} docker container
	@echo -n "Check mysql replica {{ container }} seconds behind master is lower than 60 seconds: "
    # Ok if seconds behind master is lower than 60 seconds
	@echo 'show slave status \G' | MYSQL_PWD="{{ openark_orchestrator_client_password }}" mysql -u {{ openark_orchestrator_client_user }} --host 127.0.0.1 --port {{ config.ingress_port }} | egrep "Seconds_Behind_Master: [0-5][0-9]?" > /dev/null
	@echo "OK"
.PHONY: healthcheck-mysql-replica-{{ container }}

{% endif %}
{% endfor %}
{% for _site, config in richie_sites.items() %}
BACKUP_FILE_{{ _site }} ?= richie-{{ _site }}-mysql-db-backup.sql.gz
backup-mysql-{{ _site }}: ## backup mysql db of {{ _site }} site
	@echo -n 'Backing up MySQL database of {{ _site }}'
	@rm -f ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})
	@MYSQL_PWD="{{ richie_MYSQL_ROOT_PASSWORD}}" /usr/bin/mysqldump -u root --host 127.0.0.1 --port {{ richie_mysql_primary.ingress_port }} --single-transaction {{ config.app_environment_variables.DB_NAME }} | gzip -c -9  > ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }})
	@echo 'Done! File: $(BACKUP_FILE_{{ _site }})'
.PHONY: backup-mysql-{{ _site }}

restore-mysql-{{ _site }}: ## restore mysql db of {{ _site }} site
	@echo -n 'Loading to {{ config.app_environment_variables.DB_NAME }} MySQL database the backfile $(BACKUP_FILE_{{ _site }}) '
	@cat ${ROOT_DIR}/$(BACKUP_FILE_{{ _site }}) | gzip -d | MYSQL_PWD="{{ richie_MYSQL_ROOT_PASSWORD }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ richie_mysql_primary.ingress_port }} {{ config.app_environment_variables.DB_NAME }}
	@echo 'Done!'
.PHONY: restore-mysql-{{ _site }}

{% endfor %}

{% for container, config in richie_mysql_containers.items() %}
healthcheck-mysql-port-{{ container }}: ## check mysql port for {{ container }}
	@echo -n "Check mysql port for {{ container }}: "
	@nc -z 127.0.0.1 {{ config.ingress_port }}
	@echo "OK"
.PHONY: healthcheck-port-{{ container }}
{% endfor %}

#######################
# Elasticsearch
#######################

{% for container, config in richie_elasticsearch_containers.items() %}
healthcheck-{{ container }}: ## Run elasticsearch healthcheck cluster on {{ richie_docker_deploy_stack_name }}_{{ container }} container
	@echo -n "Check Elasticsearch {{ container }}: "
	@test $$(docker exec -u root $$(docker ps -q -f name={{ richie_docker_deploy_stack_name }}_{{ container }}) curl --silent -X GET '127.0.0.1:9200/_cluster/health?pretty' | grep 'number_of_nodes' | egrep -o '[0-9]+') -eq {{ richie_elasticsearch_containers.keys() | length }}
	@test $$(docker exec -u root $$(docker ps -q -f name={{ richie_docker_deploy_stack_name }}_{{ container }}) curl --silent -X GET '127.0.0.1:9200/_cluster/health?level=shards&pretty' | egrep -o "status.*\," | sort | uniq | egrep -o "\"[^\ ]+\"") = "\"green\""
	@echo "OK"
.PHONY: healthcheck-{{ container }}

{% endfor %}

healthcheck-elasticsearch: ## Run elastic search healthcheck cluster using load balancer
	@echo -n "Check elasticsearch cluster: "
	@test $$(curl --silent 'http://localhost:{{ richie_load_balancer_haproxy_elasticsearch_port }}/_cluster/health?pretty' | grep 'number_of_nodes' | egrep -o '[0-9]+') -eq {{ richie_elasticsearch_containers.keys() | length }}
	@test $$(curl --silent 'http://localhost:{{ richie_load_balancer_haproxy_elasticsearch_port }}/_cluster/health?level=shards&pretty' | egrep -o "status.*\," | sort | uniq | egrep -o "\"[^\ ]+\"") = "\"green\""
	@echo "OK"
.PHONY: healthcheck-elasticsearch

#######################
# HAProxy
#######################

healthcheck-load-balancer-haproxy-statistics-port: ## check load balancer HAProxy statistics {{ richie_load_balancer_haproxy_statistics_port }} port
	@echo -n "Check load balancer HAProxy statistics port: "
	@nc -z 127.0.0.1 {{ richie_load_balancer_haproxy_statistics_port }}
	@echo "OK"
.PHONY: healthcheck-load-balancer-haproxy-statistics-port

healthcheck-load-balancer-haproxy-elasticsearch-port: ## check load balancer HAProxy elasticsearch {{ richie_load_balancer_haproxy_elasticsearch_port }} port
	@echo -n "Check load balancer HAProxy elasticsearch port: "
	@nc -z 127.0.0.1 {{ richie_load_balancer_haproxy_elasticsearch_port }}
	@echo "OK"
.PHONY: healthcheck-load-balancer-haproxy-elasticsearch-port

healthcheck-load-balancer-haproxy-redis-port: ## check load balancer HAProxy redis port
	@echo -n "Check load balancer HAProxy elasticsearch port: "
	@nc -z 127.0.0.1 {{ richie_load_balancer_haproxy_redis_port }}
	@echo "OK"
.PHONY: healthcheck-load-balancer-haproxy-redis-port

########################
# App job
########################

{% for _site, config in richie_sites.items() %}
healthcheck-{{ _site }}_app_job: ## check if the migrate and bootstrap_elasticsearch django commands have finished with success for {{ _site }} site
	@echo -n "Check {{ _site }}_app_job with django migrate and bootstrap elasticsearch commands: "
    # check if last job run has finished with complete state
	@docker service ps richie_nau_app_job --format {% raw %}'{{.CurrentState}}'{% endraw %} | head -n 1 | egrep -o "^Complete" | grep -q "Complete"
    # check if last job run has finished without any error
	@docker service ps richie_nau_app_job --format {% raw %}'{{.CurrentState}}|{{.Error}}'{% endraw %} | head -n 1 | egrep -o "\|.*" | grep -q "|"
	@echo "OK"
.PHONY: healthcheck-{{ _site }}_app_job

{% endfor %}

########################
# Stats
########################
{% for _site, config in richie_sites.items() %}
stats-{{ _site }}_nginx-requests_avg_time_last_5m_in_secs: ## Average time in seconds of the last 5 minutes requests
	@docker service logs --since 5m {{ docker_deploy_stack_name }}_{{ _site }}_nginx 2>&1 | \
	awk -F' ' '{print $$15}' | \
	grep -E "^[0-9\.]+$$" | \
	awk '{ sum += $$1 } END { if (NR > 0) { print sum/NR } else { print 0 } }'
.PHONY: stats-{{ _site }}_nginx-requests_avg_time_last_5m_in_secs

stats-{{ _site }}_nginx-requests_max_time_last_5m_in_secs: ## Time in seconds of the slowest request in the last 5 minutes
	@docker service logs --since 5m {{ docker_deploy_stack_name }}_{{ _site }}_nginx 2>&1 | \
	awk -F' ' '{print $$15}' | \
	grep -E "^[0-9\.]+$$" | \
	awk 'BEGIN {max = 0} {if ($$1>max) max=$$1} END {print max }'
.PHONY: stats-{{ _site }}_nginx-requests_max_time_last_5m_in_secs

stats-{{ _site }}_nginx-requests_median_time_last_5m_in_secs: ## Median time in seconds of the last 5 minutes requests
	@docker service logs --since 5m {{ docker_deploy_stack_name }}_{{ _site }}_nginx 2>&1 | \
	awk -F' ' '{print $$15}' | \
	grep -E "^[0-9\.]+$$" | \
	sort -n | awk '{a[NR]=$$0}END{print(NR%2==1)?a[int(NR/2)+1]:(a[NR/2]+a[NR/2+1])/2}'
.PHONY: stats-{{ _site }}_nginx-requests_median_time_last_5m_in_secs

stats-{{ _site }}_nginx-requests_per_sec_last_5m: ## Number of requests per second on the last 5 minutes
	@docker service logs --since 5m {{ docker_deploy_stack_name }}_{{ _site }}_nginx 2>&1 | \
	awk -F' ' '{print $$15}' | \
	awk 'END { if (NR > 0) { print NR/300 } else { print 0 } }'
.PHONY: stats-{{ _site }}_nginx-requests_per_sec_last_5m

{% endfor %}
