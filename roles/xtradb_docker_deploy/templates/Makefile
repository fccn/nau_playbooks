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

# Read-only sampling of the InnoDB and Galera counters that the engine settings of nau-technical#1100 depend on. It only
# reads performance_schema and sleeps, it never writes. Run it on each node a few times during the busiest hour:
#   make xtradb-innodb-pressure INTERVAL=30
INTERVAL ?= 10

define XTRADB_SQL_INNODB_PRESSURE
SET @interval = $(INTERVAL);
SELECT
  SUM(IF(VARIABLE_NAME = 'Innodb_redo_log_current_lsn', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Innodb_log_waits', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'Innodb_buffer_pool_wait_free', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Innodb_row_lock_waits', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'Innodb_row_lock_time', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Connections', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'Aborted_connects', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Created_tmp_disk_tables', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'Table_open_cache_misses', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Slow_queries', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'wsrep_last_committed', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME IN ('wsrep_replicated_bytes', 'wsrep_received_bytes'), VARIABLE_VALUE, 0))
INTO @lsn1, @logw1, @bpwf1, @rlw1, @rlt1, @conn1, @abc1, @tmpd1, @toc1, @slow1, @seq1, @wsb1 FROM performance_schema.global_status;
DO SLEEP(@interval);
SELECT
  SUM(IF(VARIABLE_NAME = 'Innodb_redo_log_current_lsn', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Innodb_log_waits', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'Innodb_buffer_pool_wait_free', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Innodb_row_lock_waits', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'Innodb_row_lock_time', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Connections', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'Aborted_connects', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Created_tmp_disk_tables', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'Table_open_cache_misses', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Slow_queries', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'wsrep_last_committed', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME IN ('wsrep_replicated_bytes', 'wsrep_received_bytes'), VARIABLE_VALUE, 0))
INTO @lsn2, @logw2, @bpwf2, @rlw2, @rlt2, @conn2, @abc2, @tmpd2, @toc2, @slow2, @seq2, @wsb2 FROM performance_schema.global_status;
SELECT SUM(IF(VARIABLE_NAME = 'Innodb_redo_log_checkpoint_lsn', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Innodb_buffer_pool_pages_dirty', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'Innodb_buffer_pool_pages_total', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'wsrep_local_cached_downto', VARIABLE_VALUE, 0))
INTO @ckp, @dirty, @pages, @cached_downto FROM performance_schema.global_status;
SET @gcache_text = SUBSTRING_INDEX(SUBSTRING_INDEX(@@wsrep_provider_options, 'gcache.size = ', -1), ';', 1);
SET @gcache_bytes = CAST(IF(@gcache_text REGEXP '^[0-9]+[KMG]?$$', LEFT(@gcache_text, LENGTH(@gcache_text) - IF(@gcache_text REGEXP '[KMG]$$', 1, 0)), 0) AS UNSIGNED)
  * CASE RIGHT(@gcache_text, 1) WHEN 'K' THEN 1024 WHEN 'M' THEN 1048576 WHEN 'G' THEN 1073741824 ELSE 1 END;
SELECT 'redo (the redo that writers can use before they wait)' AS section, '' AS metric, '' AS value
UNION ALL SELECT '', 'redo capacity (MiB)', ROUND(@@innodb_redo_log_capacity / 1048576)
UNION ALL SELECT '', 'redo written per second (MiB/s)', ROUND((@lsn2 - @lsn1) / @interval / 1048576, 2)
UNION ALL SELECT '', 'checkpoint age now (MiB)', ROUND((@lsn2 - @ckp) / 1048576, 1)
UNION ALL SELECT '', 'checkpoint age now (% of capacity, the closer to 100 the more writers wait)', ROUND(100 * (@lsn2 - @ckp) / @@innodb_redo_log_capacity, 1)
UNION ALL SELECT '', 'seconds to fill the capacity at this rate, if nothing was flushed', IF(@lsn2 > @lsn1, ROUND((@@innodb_redo_log_capacity - (@lsn2 - @ckp)) / ((@lsn2 - @lsn1) / @interval)), NULL)
UNION ALL SELECT '', 'Innodb_log_waits in the interval (log buffer full, not the redo capacity)', @logw2 - @logw1
UNION ALL SELECT 'data files', '', ''
UNION ALL SELECT '', 'dirty pages (% of the buffer pool)', ROUND(100 * @dirty / NULLIF(@pages, 0), 1)
UNION ALL SELECT '', 'innodb_max_dirty_pages_pct / _lwm', CONCAT(@@innodb_max_dirty_pages_pct, ' / ', @@innodb_max_dirty_pages_pct_lwm)
UNION ALL SELECT '', 'innodb_io_capacity / _max', CONCAT(@@innodb_io_capacity, ' / ', @@innodb_io_capacity_max)
UNION ALL SELECT '', 'Innodb_buffer_pool_wait_free in the interval (no free page, flushing is behind)', @bpwf2 - @bpwf1
UNION ALL SELECT 'row locks', '', ''
UNION ALL SELECT '', 'lock waits per second', ROUND((@rlw2 - @rlw1) / @interval, 2)
UNION ALL SELECT '', 'average lock wait in the interval (ms)', IF(@rlw2 > @rlw1, ROUND((@rlt2 - @rlt1) / (@rlw2 - @rlw1)), 0)
UNION ALL SELECT '', 'innodb_lock_wait_timeout (s)', @@innodb_lock_wait_timeout
UNION ALL SELECT 'connections', '', ''
UNION ALL SELECT '', 'new connections per second', ROUND((@conn2 - @conn1) / @interval, 1)
UNION ALL SELECT '', 'aborted connects per second', ROUND((@abc2 - @abc1) / @interval, 2)
UNION ALL SELECT '', 'skip_name_resolve (0 = every new connection does DNS lookups)', @@skip_name_resolve
UNION ALL SELECT '', 'Threads_running / Threads_connected / Max_used / max_connections', (SELECT CONCAT(MAX(IF(VARIABLE_NAME = 'Threads_running', VARIABLE_VALUE, NULL)), ' / ', MAX(IF(VARIABLE_NAME = 'Threads_connected', VARIABLE_VALUE, NULL)), ' / ', MAX(IF(VARIABLE_NAME = 'Max_used_connections', VARIABLE_VALUE, NULL)), ' / ', @@max_connections) FROM performance_schema.global_status)
UNION ALL SELECT 'queries', '', ''
UNION ALL SELECT '', 'slow queries per second (slow_query_log / long_query_time)', CONCAT(ROUND((@slow2 - @slow1) / @interval, 2), ' (', IF(@@slow_query_log, 'on', 'off'), ' / ', @@long_query_time, ' s)')
UNION ALL SELECT '', 'temporary tables on disk per second', ROUND((@tmpd2 - @tmpd1) / @interval, 2)
UNION ALL SELECT '', 'table cache misses per second', ROUND((@toc2 - @toc1) / @interval, 2)
UNION ALL SELECT 'galera cache (how long a node can be away and still rejoin by IST)', '', ''
UNION ALL SELECT '', 'gcache.size (MiB)', ROUND(@gcache_bytes / 1048576)
UNION ALL SELECT '', 'write-sets per second / write-set MiB per second (replicated + received)', CONCAT(ROUND((@seq2 - @seq1) / @interval, 1), ' / ', ROUND((@wsb2 - @wsb1) / @interval / 1048576, 3))
UNION ALL SELECT '', 'IST window with this gcache.size at this rate (minutes)', IF(@wsb2 > @wsb1, ROUND(@gcache_bytes / ((@wsb2 - @wsb1) / @interval) / 60, 1), NULL)
UNION ALL SELECT '', 'write-sets in the cache now / minutes they cover at this rate', IF(@seq2 > @seq1, CONCAT(@seq2 - @cached_downto, ' / ', ROUND((@seq2 - @cached_downto) / ((@seq2 - @seq1) / @interval) / 60, 1)), NULL);
endef
export XTRADB_SQL_INNODB_PRESSURE

xtradb-innodb-pressure: ## InnoDB redo, flushing, row locks, connections and the Galera cache window on this node, sampled over INTERVAL seconds (default 10). Read-only
	@printf '%s\n' "$$XTRADB_SQL_INNODB_PRESSURE" | docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --table'
.PHONY: xtradb-innodb-pressure
