# Elastic search docker deploy role

This ansible role deploys an elastic search instance using a docker-compose.yml file.
This role can be deployed to multiple hosts creating an elastic search cluster.

## Cluster configuration

To create a cluster you need to define the `elasticsearch_discovery_seed_hosts` variable with all the hosts that will be part of the cluster. 
The variable should be defined has a `list` of `string`s, where each `string` should have the hostname and port, for example:

```yaml
elasticsearch_discovery_seed_hosts: 
  - host_1:9200
  - host_2:9200
```

For example if you have this small inventory:
```ini
[elasticsearch_docker_servers]
es01-dev.nau.fccn.pt         ansible_host=172.XXX.YYY.1
es02-dev.nau.fccn.pt         ansible_host=172.XXX.YYY.2
```

You can use this small Jinja2 code:
```yaml
elasticsearch_discovery_seed_hosts_tmp: "{% for elastic_host in groups['elasticsearch_docker_servers'] %}{{ hostvars[elastic_host].ansible_host }}:{{ hostvars[elastic_host].elasticsearch_http_port }}{{ ',' if not loop.last else '' }}{% endfor %}"
elasticsearch_discovery_seed_hosts: "{{ elasticsearch_discovery_seed_hosts_tmp.split(',') | list }}"
```

To generate:
```yaml
elasticsearch_discovery_seed_hosts:
  - 172.XXX.YYY.1:9200
  - 172.XXX.YYY.2:9200
```

## Cluster initialization

To initialize an Elastic Search cluster you need to run this ansible role with the 
`elasticsearch_initialization` variable with the `true` value. 
For example: 
```bash
ansible-playbook -i hosts.ini deploy.yml -e elasticsearch_initialization=true -e elasticsearch_docker_servers=true
```

