# Richie deploy role

## Initialize Elasticsearch
To initialize the elasticsearch cluster use the `richie_elasticsearch_initialization` parameter.
Run ansible with `-e richie_deploy=true -e richie_elasticsearch_initialization=true`.

## Initialize MySQL
To initialize the mysql cluster use the `richie_mysql_initialization` parameter.
Run ansible with `-e richie_deploy=true -e richie_mysql_initialization=true --tags docker_mysql_replication`

