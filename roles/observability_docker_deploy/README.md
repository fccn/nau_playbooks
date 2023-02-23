# Observability stack

The objective of this stack is to have a Logs and Metrics Processor for all the other stacks.

It uses the fluentbit tool that is super fast, lightweight, and highly scalable logging and metrics processor and forwarder.

The fluentbit receives the docker container logs from the docker daemon and process the logs. Depending on the container name it uses a different parser to split the log line string to the fluentbit structure - similar to a json with key values.

## Docker logging driver
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

## Inputs

The fluentbit receives the docker container logs from the docker daemon using the `forward` input.

The fluentbit reads multiple host operating system log files, using a volume mount.
- `/var/log/auth.log`
- `/var/log/syslog`
- `/var/log/dpkg.log`
- `/var/log/mail.log`

## Filters
It has a couple of filters that parses the messages.

1. docker_container_name_to_stack_and_service - extracts the `docker_stack` and
`docker_stack_service`
2. openedx_tracking_logs_parser - extracts the `tracking_json` with the json content of the open
edx tracking log.
3. parse_as_json - a basic parser that extracts all the tracking json to be available on fluent
bit for further processing.
4. different parsers, one for each other docker stack (staticproxy, coursecertificate, richie and
openedx), it parses the nginx logs and extract different keys, like the `code` (http status code).

## Streams
The stream use a special syntax, similar to SQL, but not so expressive.
We use a window of 5 minutes to aggregate the data and capture metrics.
It permits to count the total log lines on 5 minutes blocks,
or to calculate the average time of all requests on 5 minutes block per docker stack and service.
Each metric is storaged on a local file that is available on the first docker swarm manager.
The stack's `Makefile` has different targets that expose some of the streams metric values.

### Outputs
1. open edx tracking logs to s3
2. docker container logs to s3 - different s3 folder to different containers.
3. file output where all the aggregated metrics are stored, use the `Makefile` to view them.
