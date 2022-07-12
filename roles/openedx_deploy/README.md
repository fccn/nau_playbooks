# openedx deploy role

Parameter `openedx_mysql_initialization` is used to initialize the mysql clustering. Add `-e openedx_mysql_initialization=true` when running ansible.

Parameter `openedx_elasticsearch_initialization` is used to initialize the elasticsearch cluster. Add `-e openedx_elasticsearch_initialization=true` when running ansible on the first time you initialize the cluster.
