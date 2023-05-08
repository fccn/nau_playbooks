# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage {{ openedx_docker_deploy_compose_name }} in docker swarm
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
	docker ps -a --filter name=^{{ openedx_docker_deploy_compose_name }}
.PHONY: ps

logs: ## View logs
	docker-compose logs -f
.PHONY: logs

# View the logs of the specified service container
_%-logs:
	docker logs --timestamps --follow --tail=10 {{ openedx_docker_deploy_compose_name }}_$*

{% for _service in docker_deploy_services %}
logs-{{ _service }}: _{{ _service }}-logs ## View last 10 lines of logs of the {{ _service }} docker service
.PHONY: logs-{{ _service }}

{% endfor %}

# Open bash
_%-bash:
	@docker exec -it {{ openedx_docker_deploy_compose_name }}_$* bash

{% for _service in docker_deploy_services %}
bash-{{ _service }}: _{{ _service }}-bash ## Open bash on the current node for the {{ _service }} docker service
.PHONY: bash-{{ _service }}

{% endfor %}

# Silent mode other targets.
# To run `healthcheck` target on silient mode, run it like `make silent-healthcheck`.
# It will print "OK" if everything is fine.
silent-%:
	@$(MAKE) $* > /dev/null && echo "OK"

healthcheck-docker-containers: ## check that docker containers are on running state
	@test $$(docker ps --filter "name={{ openedx_docker_deploy_compose_name }}-*" --format {% raw %}'{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | grep "Up " | wc -l) -eq $$(docker ps --filter "name={{ openedx_docker_deploy_compose_name }}-*" {% raw %}--format '{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | wc -l) || ( echo "Check docker containers status: error" ; exit 1 )
	@echo "Check docker containers status: OK"
.PHONY: healthcheck-docker-containers

healthcheck: healthcheck-parallel ## Overall healthcheck - for parallel execution run `make --jobs 10 healthcheck`
	@echo "Everything looks: OK"
.PHONY: healthcheck-parallel

#######################
# Specific
#######################
healthcheck-parallel: \
	healthcheck-mysql-default-port \
	healthcheck-mysql-read-replica-port \
	healthcheck-redis-port \
	healthcheck-mongo-hosts-port \
	healthcheck-elasticsearch \
{% if openedx_lms_deploy %}
	healthcheck-lms-heartbeat \
{% endif %}
{% if openedx_cms_deploy %}
	healthcheck-cms-heartbeat \
{% endif %}
{% if openedx_forum_deploy %}
	healthcheck-forum-heartbeat \
{% endif %}
{% if openedx_notes_deploy %}
	healthcheck-notes-heartbeat \
{% endif %}
{% if openedx_discovery_deploy %}
	healthcheck-discovery-heartbeat \
{% endif %}
{% if openedx_insights_deploy %}
	healthcheck-insights-heartbeat \
{% endif %}
{% if openedx_analyticsapi_deploy %}
	healthcheck-analyticsapi-heartbeat \
{% endif %}
{% if openedx_smtp_deploy %}
	healthcheck-smtp-port \
{% endif %}
	healthcheck-docker-containers
.PHONY: healthcheck-parallel

#######################
# Openedx health
#######################
{% if openedx_insights_deploy %}
healthcheck-insights-heartbeat: ## check openedx insights health
	@docker exec {{ openedx_docker_deploy_compose_name }}_insights curl --silent --fail --head --resolve insights:8000:127.0.0.1 http://insights:8000/health/ | egrep --quiet "HTTP/.*200 OK" || ( echo "Check insights heartbeat: error" ; exit 1)
	@echo "Check insights heartbeat: OK"
.PHONY: healthcheck-insights-heartbeat
{% endif %}

{% if openedx_analyticsapi_deploy %}
healthcheck-analyticsapi-heartbeat: ## check openedx analyticsapi health
	@docker exec {{ openedx_docker_deploy_compose_name }}_analyticsapi curl --silent --fail --head --resolve analyticsapi:8000:127.0.0.1 http://analyticsapi:8100/health/ | egrep --quiet "HTTP/.*200 OK" || ( echo "Check analyticsapi heartbeat: error" ; exit 1 )
	@echo "Check analyticsapi heartbeat: OK"
.PHONY: healthcheck-analyticsapi-heartbeat
{% endif %}

{% if openedx_lms_deploy %}
healthcheck-lms-heartbeat: ## check openedx lms health
	@docker exec {{ openedx_docker_deploy_compose_name }}_lms curl --silent --fail --head --resolve lms:8000:127.0.0.1 http://lms:8000/heartbeat | egrep --quiet "HTTP/.*200 OK" || ( echo "Check lms heartbeat: error" ; exit 1)
	@echo "Check lms heartbeat: OK"
.PHONY: healthcheck-lms-heartbeat
{% endif %}

{% if openedx_cms_deploy %}
healthcheck-cms-heartbeat: ## check openedx cms/studio health
	@docker exec {{ openedx_docker_deploy_compose_name }}_cms curl --silent --fail --head --resolve cms:8000:127.0.0.1 http://cms:8000/heartbeat | egrep --quiet "HTTP/.*200 OK" || ( echo "Check cms heartbeat: error" ; exit 1)
	@echo "Check cms heartbeat: OK"
.PHONY: healthcheck-cms-heartbeat
{% endif %}

{% if openedx_forum_deploy %}
healthcheck-forum-heartbeat: ## check openedx forum studio health
	@docker exec {{ openedx_docker_deploy_compose_name }}_forum wget -qSO- 127.0.0.1:{{ openedx_forum_port }}/heartbeat 2>&1 | egrep --quiet "HTTP/.*200 OK" || ( echo "Check forum heartbeat: error" ; exit 1 )
	@echo "Check forum heartbeat: OK"
.PHONY: healthcheck-forum-heartbeat
{% endif %}

{% if openedx_notes_deploy %}
healthcheck-notes-heartbeat: ## check openedx notes health
	@docker exec {{ openedx_docker_deploy_compose_name }}_notes bash -c 'exec 3<>/dev/tcp/127.0.0.1/{{ openedx_notes_port }} && echo -e "GET /heartbeat/ HTTP/1.1\r\nHost: notes\r\nConnection: close\r\n\r\n" >&3 && cat <&3 2>&1 | grep --quiet "HTTP/1.1 200 OK"' || ( echo "Check notes heartbeat: error" ; exit 1 )
	@echo "Check notes heartbeat: OK"
.PHONY: healthcheck-notes-heartbeat
{% endif %}

{% if openedx_discovery_deploy %}
healthcheck-discovery-heartbeat: ## check openedx discovery health
	@docker exec {{ openedx_docker_deploy_compose_name }}_discovery curl --silent --fail --head --resolve discovery:8000:127.0.0.1 http://discovery:8000/health/ | egrep --quiet "HTTP/.*200 OK" || ( echo "Check discovery heartbeat: error" ; exit 1 )
	@echo "Check discovery heartbeat: OK"
.PHONY: healthcheck-discovery-heartbeat
{% endif %}

{% if openedx_smtp_deploy %}
healthcheck-smtp-port: ## check openedx smtp health
	@docker exec {{ openedx_docker_deploy_compose_name }}_smtp nc -z 127.0.0.1 8025 || ( echo "Check smtp port: error connecting" ; exit 1 )
	@echo "Check smtp port: OK"
.PHONY: healthcheck-smtp-port
{% endif %}

#######################
# MySQL
#######################
healthcheck-mysql-default-port: ## check mysql port for default primary
	@nc -z {{ openedx_docker_deploy_mysql_default_host }} {{ openedx_docker_deploy_mysql_default_port }} || ( echo "Check mysql primary: error connecting {{ openedx_docker_deploy_mysql_default_host }}:{{ openedx_docker_deploy_mysql_default_port }}" ; exit 1 )
	@echo "Check mysql primary port: OK"
.PHONY: healthcheck-mysql-default-port

healthcheck-mysql-read-replica-port: ## check mysql port for read replica
	@nc -z {{ openedx_docker_deploy_mysql_read_replica_host }} {{ openedx_docker_deploy_mysql_read_replica_port }} || ( echo "Check mysql read replica port: error connecting {{ openedx_docker_deploy_mysql_read_replica_host }}:{{ openedx_docker_deploy_mysql_read_replica_port }}" ; exit 1 )
	@echo "Check mysql read replica port: OK"
.PHONY: healthcheck-mysql-read-replica-port

#######################
# Redis
#######################
healthcheck-redis-port: ## check Redis port
	@nc -z {{ openedx_docker_deploy_cache_redis_host }} {{ openedx_docker_deploy_cache_redis_port }} || ( echo "Check redis port: error connecting to {{ openedx_docker_deploy_cache_redis_host }}:{{ openedx_docker_deploy_cache_redis_port }}" ; exit 1 )
	@echo "Check redis port: OK"
.PHONY: healthcheck-redis-port

#######################
# Elasticsearch
#######################
healthcheck-elasticsearch: ## Run elastic search healthcheck cluster
	@test $$(curl --silent '{{ openedx_docker_deploy_elasticsearch_cluster_hosts_url[0] }}/_cluster/health?pretty' | grep 'number_of_nodes' | egrep -o '[0-9]+') -eq {{ openedx_docker_deploy_elasticsearch_cluster_hosts_url | length }} || ( echo "Check elasticsearch cluster: error failed number of healthy nodes" ; exit 1 )
	@test $$(curl --silent '{{ openedx_docker_deploy_elasticsearch_cluster_hosts_url[0] }}/_cluster/health?level=shards&pretty' | egrep -o "status.*\," | sort | uniq | egrep -o "\"[^\ ]+\"") = "\"green\"" || ( echo "Check elasticsearch cluster: error shards not green" ; exit 1 )
{% for es in openedx_docker_deploy_elasticsearch_cluster_hosts_url %}
	@test $$(curl -sLI {{ es }} -o /dev/null -w '%{http_code}\n') -eq 200 || ( echo "Check elasticsearch cluster: error node {es} not ok" ; exit 1 )
{% endfor %}
	@echo "Check elasticsearch cluster: OK"
.PHONY: healthcheck-elasticsearch

#######################
# Mongo
#######################
healthcheck-mongo-hosts-port: # Check if all mongo hosts port is up
{% for mongo_host in EDXAPP_MONGO_HOSTS %}
	@nc -z {{ mongo_host }} {{ EDXAPP_MONGO_PORT }} || ( echo "Check mongo port: error connecting {{ mongo_host }}:{{ EDXAPP_MONGO_PORT }}" ; exit 1)
{% endfor %}
	@echo "Check mongo cluster ports: OK"
.PHONY: healthcheck-mongo-hosts-port

#######################
# Nginx
#######################
check-config-nginx: # Check nginx configuration and its certificates
	@docker-compose exec nginx nginx -t
.PHONY: check-config-nginx

reload-nginx: # Reload nginx configuration and its certificates
	@docker-compose exec nginx nginx -s reload
.PHONY: check-config-nginx
