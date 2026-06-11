# ClickHouse docker deploy role

This ansible role deploys an ClickHouse instance using a docker-compose.yml file.

## Required Variable

You have to configure this variables:
- `clickhouse_password`

## Deploy
To deploy clickhouse run:

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit clickhouse_servers -e clickhouse_deploy=true
```

## Troubleshooting

During the deployment, if there is any issue with "Create folders" task, because of the running container, then you can just skip the folder creation and change ownership of those files with:

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit clickhouse_servers -e clickhouse_deploy=true -e '{"docker_deploy_folders": []}'
```

### Performance ClickHouse async insert setting

This configures the `ch_lrs` ClickHouse user to use **asynchronous inserts** — a performance optimization that batches small inserts together rather than writing synchronously on every row.

```bash
docker exec clickhouse clickhouse-client --query "
ALTER USER ch_lrs SETTINGS
    async_insert = 1,
    wait_for_async_insert = 0;"

```
