# Percona XtraDB docker deploy role

This ansible role deploys an Percona XtraDB instance using a docker-compose.yml file.
This role can be deployed to multiple hosts creating an Percona XtraDB cluster.

## Required Variable

You have to configure this variable:
- `xtradb_mysql_root_password`

## Certificates

Prior to deploy this role, you need to generate certificates.
This will create a `cert` folder with multiple files related to certificates.

```bash
mkdir -m 777 -p ./cert && docker run --name pxc-cert --rm -v ./cert:/cert percona/percona-xtradb-cluster:8.0 mysql_ssl_rsa_setup -d /cert
```

Then you need to configure ansible to use those files and then configure the use of this role with:

```yaml
vars:
  xtradb_certs_ca_key: /path/to/ca-key.pem
  xtradb_certs_ca: /path/to/ca.pem
  xtradb_certs_client_cert: /path/to/client-cert.pem
  xtradb_certs_client: /path/to/client-key.pem
  xtradb_certs_private_key: /path/to/private_key.pem
  xtradb_certs_public_key: /path/to/public_key.pem
  xtradb_certs_server_cert: /path/to/server-cert.pem
  xtradb_certs_server_key: /path/to/server-key.pem
```

## Cluster initialization

To create a cluster you need firstly deploy to an empty node.
Then for the next nodes you need to deploy with the variables:
-  `xtradb_cluster_initialization` with `True`.
-  `xtradb_cluster_join` with a value of the host name or IP address of the first node deployed;

Example to get the first cluster node host name or IP address:
```yaml
xtradb_cluster_join: "{{ hostvars[groups['xtradb_servers'][0]].ansible_host }}"
```

## References

- https://docs.percona.com/percona-xtradb-cluster/8.0/docker.html

## Example

Deploy first node, then join all other other nodes, then just run a normal deploy without the initialization.

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers[0]' -e xtradb_deploy=true -e xtradb_cluster_initialization=true
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers:!xtradb_servers[0]' -e xtradb_deploy=true -e serial_number=10
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers' -e xtradb_deploy=true
```

To add a new node to existing cluster add it to the `xtradb_servers` group, then deploy to it.
After that deploy and joining to existing cluster, the existing nodes should know it for on the CLUSTER_JOIN string, so we need to deploy all nodes again:
```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit new_node -e xtradb_deploy=true
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit 'xtradb_servers' -e xtradb_deploy=true
```
