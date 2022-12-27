healthcheck: ## Overall healthcheck
healthcheck: \
	healthcheck-replicas \
	healthcheck-tasks
	@echo "Everything looks: OK"
.PHONY: healthcheck
