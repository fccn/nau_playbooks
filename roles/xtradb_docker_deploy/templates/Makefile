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

# Read-only sampling targets used to judge how much of this node's work is reads and whether Galera flow
# control is throttling writes. They only read performance_schema and sleep, they never write.
# Usage: make xtradb-read-write-mix INTERVAL=30
INTERVAL ?= 10
SCHEMA ?= edxapp

define XTRADB_SQL_READ_WRITE_MIX
SET @interval = $(INTERVAL);
SELECT
  SUM(IF(EVENT_NAME = 'statement/sql/select', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/select', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/insert', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/insert', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/update', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/update', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/delete', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/delete', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/replace', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/replace', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/commit', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/commit', SUM_TIMER_WAIT, 0))
INTO @sel_n1, @sel_t1, @ins_n1, @ins_t1, @upd_n1, @upd_t1, @del_n1, @del_t1, @rep_n1, @rep_t1, @com_n1, @com_t1
FROM performance_schema.events_statements_summary_global_by_event_name;
SELECT SUM(IF(VARIABLE_NAME = 'Questions', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Innodb_rows_read', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME IN ('Innodb_rows_inserted', 'Innodb_rows_updated', 'Innodb_rows_deleted'), VARIABLE_VALUE, 0))
INTO @questions1, @rows_read1, @rows_changed1 FROM performance_schema.global_status;
DO SLEEP(@interval);
SELECT
  SUM(IF(EVENT_NAME = 'statement/sql/select', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/select', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/insert', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/insert', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/update', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/update', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/delete', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/delete', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/replace', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/replace', SUM_TIMER_WAIT, 0)),
  SUM(IF(EVENT_NAME = 'statement/sql/commit', COUNT_STAR, 0)), SUM(IF(EVENT_NAME = 'statement/sql/commit', SUM_TIMER_WAIT, 0))
INTO @sel_n2, @sel_t2, @ins_n2, @ins_t2, @upd_n2, @upd_t2, @del_n2, @del_t2, @rep_n2, @rep_t2, @com_n2, @com_t2
FROM performance_schema.events_statements_summary_global_by_event_name;
SELECT SUM(IF(VARIABLE_NAME = 'Questions', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'Innodb_rows_read', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME IN ('Innodb_rows_inserted', 'Innodb_rows_updated', 'Innodb_rows_deleted'), VARIABLE_VALUE, 0))
INTO @questions2, @rows_read2, @rows_changed2 FROM performance_schema.global_status;
SELECT 'SELECT' AS statement, ROUND((@sel_n2 - @sel_n1) / @interval, 1) AS per_second, ROUND((@sel_t2 - @sel_t1) / 1000000000000 / @interval, 3) AS avg_running
UNION ALL SELECT 'INSERT', ROUND((@ins_n2 - @ins_n1) / @interval, 1), ROUND((@ins_t2 - @ins_t1) / 1000000000000 / @interval, 3)
UNION ALL SELECT 'UPDATE', ROUND((@upd_n2 - @upd_n1) / @interval, 1), ROUND((@upd_t2 - @upd_t1) / 1000000000000 / @interval, 3)
UNION ALL SELECT 'DELETE', ROUND((@del_n2 - @del_n1) / @interval, 1), ROUND((@del_t2 - @del_t1) / 1000000000000 / @interval, 3)
UNION ALL SELECT 'REPLACE', ROUND((@rep_n2 - @rep_n1) / @interval, 1), ROUND((@rep_t2 - @rep_t1) / 1000000000000 / @interval, 3)
UNION ALL SELECT 'COMMIT', ROUND((@com_n2 - @com_n1) / @interval, 1), ROUND((@com_t2 - @com_t1) / 1000000000000 / @interval, 3);
SELECT 'SELECT share of reads + writes, by count (%)' AS metric,
  ROUND(100 * (@sel_n2 - @sel_n1) / NULLIF((@sel_n2 - @sel_n1) + (@ins_n2 - @ins_n1) + (@upd_n2 - @upd_n1) + (@del_n2 - @del_n1) + (@rep_n2 - @rep_n1), 0), 1) AS value
UNION ALL SELECT 'SELECT share of reads + writes, by execution time (%)',
  ROUND(100 * (@sel_t2 - @sel_t1) / NULLIF((@sel_t2 - @sel_t1) + (@ins_t2 - @ins_t1) + (@upd_t2 - @upd_t1) + (@del_t2 - @del_t1) + (@rep_t2 - @rep_t1), 0), 1)
UNION ALL SELECT 'statements per second (Questions)', ROUND((@questions2 - @questions1) / @interval, 1)
UNION ALL SELECT 'InnoDB rows read per second', ROUND((@rows_read2 - @rows_read1) / @interval, 1)
UNION ALL SELECT 'InnoDB rows inserted + updated + deleted per second', ROUND((@rows_changed2 - @rows_changed1) / @interval, 1);
SELECT VARIABLE_NAME AS metric, VARIABLE_VALUE AS now FROM performance_schema.global_status
WHERE VARIABLE_NAME IN ('Threads_running', 'Threads_connected', 'Max_used_connections') ORDER BY VARIABLE_NAME;
endef
export XTRADB_SQL_READ_WRITE_MIX

define XTRADB_SQL_FLOW_CONTROL
SET @interval = $(INTERVAL);
SELECT
  SUM(IF(VARIABLE_NAME = 'wsrep_flow_control_paused_ns', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'wsrep_flow_control_sent', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'wsrep_flow_control_recv', VARIABLE_VALUE, 0))
INTO @paused1, @sent1, @recv1 FROM performance_schema.global_status;
DO SLEEP(@interval);
SELECT
  SUM(IF(VARIABLE_NAME = 'wsrep_flow_control_paused_ns', VARIABLE_VALUE, 0)), SUM(IF(VARIABLE_NAME = 'wsrep_flow_control_sent', VARIABLE_VALUE, 0)),
  SUM(IF(VARIABLE_NAME = 'wsrep_flow_control_recv', VARIABLE_VALUE, 0))
INTO @paused2, @sent2, @recv2 FROM performance_schema.global_status;
SELECT ROUND(100 * (@paused2 - @paused1) / (@interval * 1000000000), 3) AS paused_pct_of_interval,
  @sent2 - @sent1 AS pauses_sent_by_this_node, @recv2 - @recv1 AS pauses_received_from_peers;
SELECT VARIABLE_NAME AS metric, VARIABLE_VALUE AS now FROM performance_schema.global_status
WHERE VARIABLE_NAME IN ('wsrep_local_state_comment', 'wsrep_cluster_size', 'wsrep_cluster_status', 'wsrep_ready',
  'wsrep_local_recv_queue', 'wsrep_local_recv_queue_max', 'wsrep_local_recv_queue_avg', 'wsrep_local_send_queue',
  'wsrep_local_send_queue_avg', 'wsrep_cert_deps_distance', 'wsrep_apply_window', 'wsrep_commit_window',
  'wsrep_local_cert_failures', 'wsrep_local_bf_aborts', 'wsrep_flow_control_paused') ORDER BY VARIABLE_NAME;
SELECT @@wsrep_applier_threads AS applier_threads, @@wsrep_sync_wait AS sync_wait, @@max_connections AS max_connections,
  ROUND(@@innodb_buffer_pool_size / 1048576) AS buffer_pool_mb,
  SUBSTRING_INDEX(SUBSTRING_INDEX(@@wsrep_provider_options, 'gcs.fc_limit = ', -1), ';', 1) AS fc_limit,
  SUBSTRING_INDEX(SUBSTRING_INDEX(@@wsrep_provider_options, 'gcs.fc_master_slave = ', -1), ';', 1) AS fc_master_slave;
endef
export XTRADB_SQL_FLOW_CONTROL

define XTRADB_SQL_STATEMENT_TIME_SHARE
SELECT kind, SUM(COUNT_STAR) AS calls, ROUND(SUM(SUM_TIMER_WAIT) / 1000000000000, 1) AS total_seconds,
  ROUND(100 * SUM(SUM_TIMER_WAIT) / NULLIF(SUM(SUM(SUM_TIMER_WAIT)) OVER (), 0), 1) AS pct_of_time, SUM(SUM_ROWS_EXAMINED) AS rows_examined
FROM (
  SELECT CASE
      WHEN DIGEST_TEXT LIKE 'SELECT %FOR UPDATE%' OR DIGEST_TEXT LIKE 'SELECT %FOR SHARE%' THEN 'SELECT FOR UPDATE/SHARE (stays on the writer)'
      WHEN DIGEST_TEXT LIKE 'SELECT %' THEN 'SELECT'
      WHEN DIGEST_TEXT LIKE 'INSERT %' OR DIGEST_TEXT LIKE 'REPLACE %' THEN 'INSERT/REPLACE'
      WHEN DIGEST_TEXT LIKE 'UPDATE %' THEN 'UPDATE'
      WHEN DIGEST_TEXT LIKE 'DELETE %' THEN 'DELETE'
      ELSE 'other (COMMIT, SET, BEGIN, SHOW...)' END AS kind,
    COUNT_STAR, SUM_TIMER_WAIT, SUM_ROWS_EXAMINED
  FROM performance_schema.events_statements_summary_by_digest
  WHERE DIGEST_TEXT IS NOT NULL AND ('$(SCHEMA)' = '' OR SCHEMA_NAME = '$(SCHEMA)')
) AS digests GROUP BY kind ORDER BY total_seconds DESC;
SELECT LEFT(DIGEST_TEXT, 150) AS top_statements_by_total_time, COUNT_STAR AS calls, ROUND(SUM_TIMER_WAIT / 1000000000000, 1) AS total_seconds,
  ROUND(AVG_TIMER_WAIT / 1000000000, 2) AS avg_ms, SUM_ROWS_EXAMINED AS rows_examined
FROM performance_schema.events_statements_summary_by_digest
WHERE DIGEST_TEXT IS NOT NULL AND ('$(SCHEMA)' = '' OR SCHEMA_NAME = '$(SCHEMA)')
ORDER BY SUM_TIMER_WAIT DESC LIMIT 10;
endef
export XTRADB_SQL_STATEMENT_TIME_SHARE

xtradb-read-write-mix: ## Reads vs writes on this node, by count and execution time, sampled over INTERVAL seconds (default 10). Read-only
	@printf '%s\n' "$$XTRADB_SQL_READ_WRITE_MIX" | docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --table'
.PHONY: xtradb-read-write-mix

xtradb-flow-control: ## Galera flow control and receive queue on this node, sampled over INTERVAL seconds (default 10). Read-only
	@printf '%s\n' "$$XTRADB_SQL_FLOW_CONTROL" | docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --table'
.PHONY: xtradb-flow-control

xtradb-statement-time-share: ## Share of execution time by statement type and top statements since start, for SCHEMA (default edxapp, SCHEMA= for all). Read-only
	@printf '%s\n' "$$XTRADB_SQL_STATEMENT_TIME_SHARE" | docker exec -i {{ xtradb_docker_container_name }} bash -c 'MYSQL_PWD="{{ xtradb_mysql_root_password }}" /usr/bin/mysql -u root --host 127.0.0.1 --port {{ xtradb_mysql_port }} --table'
.PHONY: xtradb-statement-time-share

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