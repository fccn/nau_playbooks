# Observability ansible role

The objective of this ansible role is to have a Logs and Metrics Processor for all the other NAU projects.

It uses the Fluent Bit tool that is super fast, lightweight, and highly scalable logging and metrics processor and forwarder.

The Fluent Bit receives the docker container logs from the docker daemon and process the logs. Depending on the container name it uses a different parser to split the log line string to the Fluent Bit structure - similar to a json with key values.

## Docker logging driver
The docker daemon should be configured to use the `fluentd` logging driver. It should use the
`localhost:24224` on the `fluentd-address`.

Docker daemon json file has yaml:
```yaml
  log-driver: fluentd
  log-opts:
    fluentd-address: "localhost:24224"
    fluentd-async: "true"
    tag: "docker.container.log.{% raw %}{{if (index .ContainerLabels \"com.docker.swarm.service.name\")}}{{index .ContainerLabels \"com.docker.swarm.service.name\"}}{{end}}{% endraw %}{% raw %}{{if (index .ContainerLabels \"com.docker.compose.project\")}}{{index .ContainerLabels \"com.docker.compose.project\"}}_{{end}}{% endraw %}{% raw %}{{if (index .ContainerLabels \"com.docker.compose.service\")}}{{index .ContainerLabels \"com.docker.compose.service\"}}{{end}}{% endraw %}"
```

You should execute a docker version that has support for the dual logging feature.
So all log messages are accessible also using the `docker logs` command.

The Fluent Bit then uses the field `container_name` on the match of its filters to apply to correct filter.

Reference: https://docs.docker.com/config/containers/logging/fluentd/

## Inputs

The Fluent Bit receives the docker container logs from the docker daemon using the `forward` input.

The Fluent Bit reads multiple host operating system log files, using a volume mount.
- `/var/log/auth.log`
- `/var/log/syslog`
- `/var/log/dpkg.log`
- `/var/log/mail.log`

## Filters
It has a couple of filters that parses the messages.

* `docker_container_name_to_project_and_service` - extracts the `docker_project` and
`docker_service` that are then used inside of the stream processor phase.
* `openedx_tracking_logs_parser` - extracts the `tracking_json` field that is a JSON with the content as the Open edX tracking log.
* `parse_as_json` - a basic parser that extracts all the tracking json to be available on fluent
bit for further processing.
* different parsers, one for each other docker projects (staticproxy, coursecertificate, richie and
openedx), it parses the nginx logs and extract different keys, like the `code` (http status code).

## Streams
The stream use a special syntax, similar to SQL, but not so expressive.
We use a window of 5 minutes to aggregate the data and capture metrics.
It permits to count the total log lines on 5 minutes blocks,
or to calculate the average time of all requests on 5 minutes block per docker project and service.
Each metric is storaged on a local file that is available on the first docker swarm manager.
The project's `Makefile` has different targets that expose some of the streams metric values.

### Outputs
1. open edx tracking logs to s3
2. docker container logs to s3 - different s3 folder to different containers.
3. file output where all the aggregated metrics are stored, use the `Makefile` to view them.
