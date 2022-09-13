# Openedx deploy role

## Initialize Elasticsearch
To initialize the elasticsearch cluster use the `openedx_elasticsearch_initialization` parameter.
Run ansible with `-e openedx_deploy=true -e openedx_elasticsearch_initialization=true`.

## Initialize MySQL
To initialize the mysql cluster use the `openedx_mysql_initialization` parameter.
Run ansible with `-e openedx_deploy=true -e openedx_mysql_initialization=true --tags docker_mysql_replication`

## Database Migrations

If you want to run database migrations for the LMS, add the next parameters when running ansible:
```bash
-e openedx_deploy=true -e openedx_lms_migrate=true 
```

To run DB migrations for the Studio/cms application:
```bash
-e openedx_deploy=true -e openedx_cms_migrate=true 
```

To re-index all the courses:
```bash
-e openedx_deploy=true -e openedx_cms_reindex_all_courses=true 
```

The same thing for forum:
```bash
-e openedx_deploy=true -e openedx_forum_job=true 
```

Notes
```bash
-e openedx_deploy=true -e openedx_notes_job=true 
```
And discovery:
```bash
-e openedx_deploy=true -e openedx_discovery_job=true
```

To run all database migrations on every application, run:
```bash
-e openedx_deploy=true -e openedx_app_job=true -e openedx_forum_job=true -e openedx_notes_job=true -e openedx_discovery_job=true
```

## Re-index

To re-index the courses on the new elastic search cluster instance, deploy with this extra ansible parameters:

```python
-e openedx_deploy=true -e openedx_app_job=true -e openedx_cms_reindex_all_courses=true
```
