# Docker execute

This role allows to run a command inside the a docker container.

Example:
```yaml
- name: Print all django commands available for a service that runs on a stack
  include_role:
    name: docker_execute
  vars:
    docker_exec_name: <name of the execution>
    docker_container_name: <name of the docker container to execute the command>
    docker_exec_command: python manage.py --help
```

Additionally you can use the additional variables `docker_exec_ignore_errors` and  `docker_exec_output_fact` to ignore errors and get its output to a fact, so you can print on other way.
