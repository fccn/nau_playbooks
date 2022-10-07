# Docker exec in swarm

This role allows to run a command inside the first container for a docker service swarm.

It assumes that all the docker swarm nodes are configured on the ansible inventory.

1. It finds the docker swarm node where it's running the first container.
2. Executes different verifications, like check if the docker swarm node exist on the inventory and check if the container is on the `Running` state.
3. Then executes the real command, defined by the `docker_exec_command` variable.
4. It prints command output nicely.
5. It has an option to ignore errors, `docker_exec_ignore_errors`.
6. And it is possible to define an ansible fact with the command output for advanced usages, `docker_exec_output_fact`.

Example, replace `stack_service` with something like `openedx_lms` for a stack name `openedx` with a docker service named `lms`.
```yaml
- name: Print all django commands available for a service that runs on a stack
  include_role:
    name: docker_exec_in_swarm
  vars:
    docker_stack: <stack_name>
    docker_service_to_exec: <stack_service>
    docker_exec_command: python manage.py --help
```
