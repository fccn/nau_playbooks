# Makefile with helper commands to manage openedx docker swarm

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

# -- Rules
default: help

deploy: ## deploy docker stack
	docker stack deploy openedx --compose-file docker-stack.yml
.PHONY: deploy

service-ls: ## list the docker service
	docker service ls
.PHONY: ls

mysql-primary-status: ## show primary master status
	echo 'show slave status \G' | mysql -u root --host 127.0.0.1 --port 3306 -p
.PHONY: mysql-slave-status

mysql-replica-status: ## show replica slave status
	echo 'show slave status \G' | mysql -u root --host 127.0.0.1 --port 3307 -p
.PHONY: mysql-slave-status

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
