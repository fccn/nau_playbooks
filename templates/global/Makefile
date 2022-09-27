# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage all the docker stacks on swarm
###################################################################################################


ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

healthcheck: ## All stacks healthchecks
	@echo -n "Check staticproxy stack: "
	@$(MAKE) -C staticproxy       healthcheck > /dev/null
	@echo "ok"
	@echo -n "Check coursecertificate stack: "
	@$(MAKE) -C coursecertificate healthcheck > /dev/null
	@echo "ok"
	@echo -n "Check openedx stack: "
	@$(MAKE) -C openedx           healthcheck > /dev/null
	@echo "ok"
	@echo -n "Check richie stack: "
	@$(MAKE) -C richie            healthcheck > /dev/null
	@echo "ok"
	@echo -n "Check observability stack: "
	@$(MAKE) -C observability     healthcheck > /dev/null
	@echo "ok"
	@echo "Everything looks: OK"
.PHONY: healthcheck
