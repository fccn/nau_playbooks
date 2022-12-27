
{% for _metric in observability_fluentbit_metrics %}
{{ _metric | replace(".", "-") }}: ## To view the metric value execute: `make stack=staticproxy service=nginx {{ _metric | replace(".", "-") }}`
# Get the value for the metric, but prevent to return a too old value.
# Get the last matched line for the stack and service if the time is on the last 15 minutes, get the value, if not return zero.
	@tac {{ observability_fluentbit_aggregator_data }}output-files/{{ _metric }} | grep -m1 '"$(stack)","$(service)"' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$4; else print 0}'
.PHONY: {{ _metric | replace(".", "-") }}

{% endfor %}

# per second metric for total metrics that don't apply a function like average or maximum.
{% for _metric in observability_fluentbit_metrics_total %}
{{ _metric | replace(".", "-") }}-per-second: ## To view the metric value execute: `make stack=staticproxy service=nginx {{ _metric | replace(".", "-") }}-per-second`
# The same has the normal
	@tac {{ observability_fluentbit_aggregator_data }}output-files/{{ _metric }} | grep -m1 '"$(stack)","$(service)"' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$4/300; else print 0}'
.PHONY: {{ _metric | replace(".", "-") }}-per-second

{% endfor %}

metrics-requests-last5m-code: ## To view the metric value execute: `make stack=staticproxy service=nginx code=301 metrics-requests-last5m-code`
	@tac {{ observability_fluentbit_aggregator_data }}/output-files/metrics.requests.last5m.code | grep -m1 '"$(stack)","$(service)",$(code)' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$5; else print 0}'
.PHONY: metrics-requests-last5m-code

metrics-requests-last5m-code-per-second: ## To view the metric value execute: `make stack=staticproxy service=nginx code=301 metrics-requests-last5m-code-per-second`
# The same has the normal
	@tac {{ observability_fluentbit_aggregator_data }}/output-files/metrics.requests.last5m.code | grep -m1 '"$(stack)","$(service)",$(code)' | awk -F',' '{match($$1,/^([0-9]+)(.)([0-9]+)$$/,d); "date +%s --date \"-15 min\"" | getline dtm15; if(dtm15 < d[1]) print $$5/300; else print 0}'
.PHONY: metrics-requests-last5m-code-per-second
