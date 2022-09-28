# Observability stack

The objective of this stack is to have a Logs and Metrics Processor for all the other stacks.

## Required Variables

This variable needs to be defined.
- `observability_fluentbit_aggregator_host_fqdn`

We recommend to be the first docker swarm manager.
```yaml
observability_fluentbit_aggregator_host_fqdn: "{{ groups['nau_docker_swarm_managers'][0] }}"
```

### Docker logging driver
The docker daemon should be configured to use the `fluentd` logging driver. It should use the
`localhost:24224` on the `fluentd-address`.

Docker daemon json file has yaml:
```yaml
  log-driver: fluentd
  log-opts:
    fluentd-address: "localhost:24224"
    fluentd-async: "true"
    tag: "docker.container.log.{% raw %}{{if (index .ContainerLabels \"com.docker.swarm.service.name\")}}{{index .ContainerLabels \"com.docker.swarm.service.name\"}}{{end}}{% endraw %}"
```

You should execute a docker version that has support for the dual logging feature.
So all log messages are accessible also using the `docker logs` command.

### Relay
The `observability_fluentbit-relay` docker container is used to monitor the host operating system
important log files and to relay the docker daemon messages to the central aggregator.

### Aggregator
The `observability_fluentbit-aggregator` docker container is executed on the host of the value
of the variable `observability_fluentbit_aggregator_host_fqdn`, we recommend to be the first
docker swarm manager.

#### Inputs
This service aggregates all the messages relayed by the `observability_fluentbit-relay` containers
that it has only an `input` that is a `forward`.

#### Filters
It has a couple of filters that parses the messages.

1. docker_container_name_to_stack_and_service - extracts the `docker_stack` and
`docker_stack_service`
2. openedx_tracking_logs_parser - extracts the `tracking_json` with the json content of the open
edx tracking log.
3. parse_as_json - a basic parser that extracts all the tracking json to be available on fluent
bit for further processing.

#### Outputs
1. open edx tracking logs to s3
2. docker container logs to s3 - different s3 folder to different containers.
