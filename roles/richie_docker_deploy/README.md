# Richie docker deploy role


```yaml
richie_deploy_run: "{{ richie_deploy | default(false) }}"
richie_docker_deploy_run: "{{ richie_docker_deploy | default(false) }}"
elasticsearch_cluster_hosts_url_tmp: "{% for elastic_host in groups['elasticsearch_docker_servers'] %}http://{{ hostvars[elastic_host].ansible_host }}:{{ hostvars[elastic_host].elasticsearch_http_port }}{{ ',' if not loop.last else '' }}{% endfor %}"
richie_docker_deploy_elasticsearch_cluster_hosts_url: "{{ elasticsearch_cluster_hosts_url_tmp.split(',') | list }}"
richie_docker_deploy_redis_host: "{{ hostvars[groups['redis_docker_servers'][0]].redis_virtual_ipv4 }}"
richie_docker_deploy_redis_port: "{{ hostvars[groups['redis_docker_servers'][0]].redis_docker_port }}"
richie_docker_deploy_redis_db: "2"
richie_docker_deploy_mysql_host: "{{ hostvars[groups['richie_mysql_docker_servers'][0]].richie_mysql_virtual_ipv4 }}"
richie_docker_deploy_mysql_port: "{{ hostvars[groups['richie_mysql_docker_servers'][0]].richie_mysql_docker_port }}"
```

## Maintenance
To mark the richie to maintenance deploy it with `-e richie_nau_app_maintenance_header_msg=true`.
This will add a link that links to the homepage with a message saying that the system is on maintenance.
The message won't be visible on the homepage.
