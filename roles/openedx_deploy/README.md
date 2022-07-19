# Openedx deploy role

## Initialize Elasticsearch
To initialize the elasticsearch cluster use the `openedx_elasticsearch_initialization` parameter.
Run ansible with `-e openedx_deploy=true -e openedx_elasticsearch_initialization=true`.

## Initialize MySQL
To initialize the mysql cluster use the `openedx_mysql_initialization` parameter.
Run ansible with `-e openedx_deploy=true -e openedx_mysql_initialization=true --tags docker_mysql_replication`

