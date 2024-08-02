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
