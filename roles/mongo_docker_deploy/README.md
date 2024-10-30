# Mongo docker deploy

Deploy Mongo DB service using a docker compose file.

This role deploys a Mongo DB service using `host` network.

Deploying a MongoDB Cluster with Docker
https://www.mongodb.com/compatibility/deploying-a-mongodb-cluster-with-docker

## Configuration

Variables:
- mongo_docker_replSet - required variable its value could be, example: `rs0`;
- mongo_docker_admin_username - required variable its value have the admin username.
- mongo_docker_admin_password - required variable its value have the admin password.
- mongo_docker_initdb_root_username - optional username value to initialize the database, example: `admin`;
- mongo_docker_initdb_root_password - optional password value to initialize the database.
- mongo_docker_keyFile_value - optional value of the MongoDB keyFile to increase security between node configuration.

## Add Members to a Replica Set
https://www.mongodb.com/docs/v3.6/tutorial/expand-replica-set/

Deploy this role to new server.

Connect to the replica set’s primary. Run this to know which is the primary.
```
ssh pers...
mongo admin -u admin -pXXXXXXX -host rs0/localhost
db.hello()
```

Add this new mongo to the replica set.
```
rs.add( { host: "<new VM>:27017", priority: 0, votes: 0 } )
```

Note: you have to add it one by one waiting for the previous one to pass from `STARTUP2` (synchronizing) to `SECONDARY` (ready) state. If you add all of them at the same time it will increase a lot the traffic of the primary node.

Ensure it reaches SECONDARY state.
```
ssh <new VM>
mongo admin -u admin -pXXXXXXX -host rs0/localhost
rs.status()
```

Deploy the new node to Mongo DB clients. On Open edX add that new node on the list of Mongo connection string.

Once the newly added member has transitioned into SECONDARY state, use rs.reconfig() to update the newly added member’s priority and votes if needed.
Update the new node:
```
var cfg = rs.conf();
cfg.members[1].priority = 1
cfg.members[1].votes = 1
rs.reconfig(cfg, {force: true})
```

In the final step to make one of the new ones primary, you can use the command `db.isMaster()` which returns a list of hosts to guide you in setting the highest priority to the node you want to make primary by using.

```
cfg = rs.conf()
cfg.members[0].priority = 0.5
cfg.members[1].priority = 1
rs.reconfig(cfg, {force: true})
```

Run `rs.status()` on older and new master to check the `PRIMARY` replica has been changed.

After lowering the `priority` of the older Mongo DB instances; then deploy the new connection to Mongo DB on its clients without the older, to be removed, instances. Then remove the old server from the cluster.

Then login into primary and remove the old server from the cluster.
```
rs.remove("<old host>")
```

Log in to each old server to remove and then shutdown it.
```
mongo -host localhost
```

Run this to shutdown it.
```
use admin
db.shutdownServer()
```

If needed disable the OS service.
```
systemctl disable mongod.service
```

After removing all the older nodes, we should upgrade the compatibility version of the cluster.
On the primary node run this:
```
db.adminCommand( { setFeatureCompatibilityVersion: "4.0" } )
```

https://www.mongodb.com/docs/manual/tutorial/expand-replica-set/


Upgrade a Replica Set to 4.0
https://www.mongodb.com/docs/manual/release-notes/4.0-upgrade-replica-set/

## Upgrade existing MongoDB Cluster

To upgrade existing MongoDB Cluster from 4.2 -> 4.4 -> 5.0 -> 6.0 -> 7.0

```bash
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit mongo_docker_servers -e mongo_deploy=true -e mongo_docker_image=docker.io/mongo:4.4 -e mongo_feature_compatibility_version=4.4 -v
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit mongo_docker_servers -e mongo_deploy=true -e mongo_docker_image=docker.io/mongo:5.0 -e mongo_feature_compatibility_version=5.0 -v
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit mongo_docker_servers -e mongo_deploy=true -e mongo_docker_image=docker.io/mongo:6.0 -e mongo_feature_compatibility_version=6.0 -e mongo_shell_command=mongosh -v
ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit mongo_docker_servers -e mongo_deploy=true -e mongo_docker_image=docker.io/mongo:7.0 -e mongo_feature_compatibility_version=7.0 -e mongo_shell_command=mongosh -e mongo_feature_compatibility_confirm=true -v
```

This role doesn't  change the "Feature Compatibility Version" of the MongoDB, because this needs to applied after changing the docker image on all existing nodes.

The `deploy.yml` ansible playbook also has a new task, with the same group of MongoDB servers, to update the "Feature Compatibility Version" after the deploy.