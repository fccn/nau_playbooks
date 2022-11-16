# Richie deploy role

## Initialize Elasticsearch
To initialize the elasticsearch cluster use the `richie_elasticsearch_initialization` parameter.
Run ansible with `-e richie_deploy=true -e richie_elasticsearch_initialization=true`.

## Initialize MySQL
To initialize the mysql cluster use the `richie_mysql_initialization` parameter.
Run ansible with `-e richie_deploy=true -e richie_mysql_initialization=true --tags docker_mysql_replication`

## Maintenance
To mark the richie to maintenance deploy it with `-e richie_nau_app_maintenance_header_msg=true`.
This will add a link that links to the homepage with a message saying that the system is on maintenance.
The message won't be visible on the homepage.
