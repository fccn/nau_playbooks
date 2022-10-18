# Openedx deploy role

## Initialize Elasticsearch
To initialize the elasticsearch cluster use the `openedx_elasticsearch_initialization` parameter.
Run ansible with `-e openedx_deploy=true -e openedx_elasticsearch_initialization=true`.

## Initialize MySQL
To initialize the mysql cluster use the `openedx_mysql_initialization` parameter.
Run ansible with `-e openedx_deploy=true -e openedx_mysql_initialization=true --tags docker_mysql_replication`

## Database Migrations
The database migrations are configured per application using the next ansible extra variables:
- openedx_lms_migrate
- openedx_cms_migrate
- openedx_forum_job
- openedx_notes_job
- openedx_discovery_job
- openedx_analyticsapi_migrate

Example to run the lms migrations:
```bash
-e openedx_deploy=true -e openedx_lms_migrate=true
```
If you need to run multiple database migrations on multiple containers, then add each variable.
For example to run on lms and studio migrations use:
```bash
-e openedx_deploy=true -e openedx_lms_migrate=true -e openedx_cms_migrate=true
```

## Re-index

To re-index the courses on the new elastic search cluster instance, deploy with this extra ansible parameters:

```python
-e openedx_deploy=true -e openedx_cms_reindex_all_courses=true
```

To re-index the content library:
```python
-e openedx_deploy=true -e openedx_cms_reindex_content_library=true
```

To re-index the library you need to run this command directly on the cms container.
```bash
SERVICE_VARIANT=cms python manage.py cms reindex_library --all --settings nau_production
```

To create the index on analytics api:
```bash
-e openedx_analyticsapi_create_elasticsearch_learners_indices=true
```
