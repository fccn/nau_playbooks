# {{ ansible_managed }}
###################################################################################################
# Makefile with helper commands to manage all the docker stacks on swarm
###################################################################################################


ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

status-healthcheck: ## All stacks healthchecks
	@echo "Check staticproxy stack"
	$(MAKE) -C staticproxy       status-healthcheck
	@echo ""
	@echo "Check coursecertificate stack"
	$(MAKE) -C coursecertificate status-healthcheck
	@echo ""
	@echo "Check openedx stack"
	$(MAKE) -C openedx           status-healthcheck
	@echo ""
	@echo "Check richie stack"
	$(MAKE) -C richie            status-healthcheck
	@echo ""
	@echo "Everything looks: OK"
.PHONY: status-healthcheck
