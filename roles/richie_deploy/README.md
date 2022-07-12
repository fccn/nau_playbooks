# Richie deploy role

Parameter `richie_mysql_initialization` is used to initialize the mysql clustering. Add `-e richie_mysql_initialization=true` when running ansible.

Parameter `richie_elasticsearch_initialization` is used to initialize the elasticsearch cluster. Add `-e richie_elasticsearch_initialization=true` when running ansible on the first time you initialize the cluster.
