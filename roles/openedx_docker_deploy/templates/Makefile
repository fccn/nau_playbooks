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
	@echo -n "Check docker containers status: "
	@test $$(docker ps --filter "name={{ openedx_docker_deploy_compose_name }}-*" --format {% raw %}'{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | grep "Up " | wc -l) -eq $$(docker ps --filter "name={{ openedx_docker_deploy_compose_name }}-*" {% raw %}--format '{{.Names}}\t{{.Status}}'{% endraw %} -a | grep -v "_job" | wc -l)
	@echo "OK"
.PHONY: healthcheck-docker-containers

#######################
# Specific
#######################
healthcheck: ## Overall healthcheck
healthcheck: \
	healthcheck-mysql-default-port \
	healthcheck-mysql-read-replica-port \
	healthcheck-redis-port \
	healthcheck-mongo-hosts-port \
	healthcheck-elasticsearch \
{% if openedx_lms_deploy %}
	healthcheck-openedx-lms-heartbeat \
{% endif %}
{% if openedx_cms_deploy %}
	healthcheck-openedx-cms-heartbeat \
{% endif %}
{% if openedx_forum_deploy %}
	healthcheck-openedx-forum-heartbeat \
{% endif %}
{% if openedx_notes_deploy %}
	healthcheck-openedx-notes-hear \
{% endif %}
{% if openedx_discovery_deploy %}
	healthcheck-openedx-discovery-heartbeat \
{% endif %}
{% if openedx_insights_deploy %}
	healthcheck-openedx-insights-heartbeat \
{% endif %}
{% if openedx_analyticsapi_deploy %}
	healthcheck-openedx-analyticsapi-heartbeat \
{% endif %}
{% if openedx_smtp_deploy %}
	healthcheck-openedx-smtp-heartbeat \
{% endif %}
	healthcheck-docker-containers
	@echo "Everything looks: OK"
.PHONY: healthcheck

#######################
# Openedx health
#######################
{% if openedx_insights_deploy %}
healthcheck-openedx-insights-heartbeat: ## check openedx insights health
	@docker exec insights curl --silent --fail --head --resolve insights:8000:127.0.0.1 http://insights:8000/health/ | egrep "HTTP/.*200 OK"
.PHONY: healthcheck-openedx-insights-heartbeat
{% endif %}

{% if openedx_analyticsapi_deploy %}
healthcheck-openedx-analyticsapi-heartbeat: ## check openedx analyticsapi health
	@docker exec analyticsapi curl --silent --fail --head --resolve analyticsapi:8000:127.0.0.1 http://analyticsapi:8100/health/ | egrep "HTTP/.*200 OK"
.PHONY: healthcheck-openedx-analyticsapi-heartbeat
{% endif %}

{% if openedx_lms_deploy %}
healthcheck-openedx-lms-heartbeat: ## check openedx lms health
	@docker exec lms curl --silent --fail --head --resolve lms:8000:127.0.0.1 http://lms:8000/heartbeat | egrep "HTTP/.*200 OK"
.PHONY: healthcheck-openedx-lms-heartbeat
{% endif %}

{% if openedx_cms_deploy %}
healthcheck-openedx-cms-heartbeat: ## check openedx cms/studio health
	@docker exec cms curl --silent --fail --head --resolve cms:8000:127.0.0.1 http://cms:8000/heartbeat | egrep "HTTP/.*200 OK"
.PHONY: healthcheck-openedx-cms-heartbeat
{% endif %}

{% if openedx_forum_deploy %}
healthcheck-openedx-forum-heartbeat: ## check openedx forum studio health
	@docker exec forum curl --silent --fail --head --resolve forum:{{ openedx_forum_port }}:127.0.0.1 http://forum:{{ openedx_forum_port }}/heartbeat | egrep "HTTP/.*200 OK"
.PHONY: healthcheck-openedx-forum-heartbeat
{% endif %}

{% if openedx_notes_deploy %}
healthcheck-openedx-notes-heartbeat: ## check openedx notes health
	@docker exec notes bash -c 'exec 3<>/dev/tcp/127.0.0.1/{{ openedx_notes_port }} && echo -e "GET /heartbeat/ HTTP/1.1\r\nHost: notes\r\nConnection: close\r\n\r\n" >&3 && cat <&3 | grep "HTTP/1.1 200 OK"'
.PHONY: healthcheck-openedx-notes-heartbeat
{% endif %}

{% if openedx_discovery_deploy %}
healthcheck-openedx-discovery-heartbeat: ## check openedx discovery health
	@docker exec discovery curl --silent --fail --head --resolve discovery:8000:127.0.0.1 http://discovery:8000/health/ | egrep "HTTP/.*200 OK"
.PHONY: healthcheck-openedx-discovery-heartbeat
{% endif %}

{% if openedx_smtp_deploy %}
healthcheck-openedx-smtp-heartbeat: ## check openedx smtp health
	@docker exec smtp echo '' > /dev/tcp/127.0.0.1/8025
.PHONY: healthcheck-openedx-smtp-heartbeat
{% endif %}

#######################
# MySQL
#######################
healthcheck-mysql-default-port: ## check mysql port for default primary
	@echo -n "Check mysql port for {{ openedx_docker_deploy_mysql_default_host }}:{{ openedx_docker_deploy_mysql_default_port }} "
	@nc -z {{ openedx_docker_deploy_mysql_default_host }} {{ openedx_docker_deploy_mysql_default_port }}
	@echo "OK"
.PHONY: healthcheck-mysql-default-port

healthcheck-mysql-read-replica-port: ## check mysql port for read replica
	@echo -n "Check mysql port for {{ openedx_docker_deploy_mysql_read_replica_host }}:{{ openedx_docker_deploy_mysql_read_replica_port }} "
	@nc -z {{ openedx_docker_deploy_mysql_read_replica_host }} {{ openedx_docker_deploy_mysql_read_replica_port }}
	@echo "OK"
.PHONY: healthcheck-mysql-read-replica-port

#######################
# Redis
#######################
healthcheck-redis-port: ## check Redis port
	@echo -n "Check redis port: "
	@nc -z {{ openedx_docker_deploy_cache_redis_host }} {{ openedx_docker_deploy_cache_redis_port }}
	@echo "OK"
.PHONY: healthcheck-redis-port

#######################
# Elasticsearch
#######################
healthcheck-elasticsearch: ## Run elastic search healthcheck cluster
	@echo -n "Check elasticsearch cluster: "
	@test $$(curl --silent '{{ openedx_docker_deploy_elasticsearch_cluster_hosts_url[0] }}/_cluster/health?pretty' | grep 'number_of_nodes' | egrep -o '[0-9]+') -eq {{ openedx_docker_deploy_elasticsearch_cluster_hosts_url | length }}
	@test $$(curl --silent '{{ openedx_docker_deploy_elasticsearch_cluster_hosts_url[0] }}/_cluster/health?level=shards&pretty' | egrep -o "status.*\," | sort | uniq | egrep -o "\"[^\ ]+\"") = "\"green\""
{% for es in openedx_docker_deploy_elasticsearch_cluster_hosts_url %}
	@test $$(curl -sLI {{ es }} -o /dev/null -w '%{http_code}\n') -eq 200
{% endfor %}
	@echo "OK"
.PHONY: healthcheck-elasticsearch

#######################
# Mongo
#######################
healthcheck-mongo-hosts-port: # Check if all mongo hosts port is up
	@echo -n "Check Mongo cluster: "
{% for mongo_host in EDXAPP_MONGO_HOSTS %}
	@nc -z {{ mongo_host }} {{ EDXAPP_MONGO_PORT }}
{% endfor %}
	@echo "OK"
.PHONY: healthcheck-mongo-hosts-port
