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
- mongo_limit_pids - thread limit of the container (cgroup `pids.max`), default `32768`. mongod uses one thread per client connection and, without this limit, the container inherits the systemd `DefaultTasksMax` of the VM (9374 on PROD), which refused new connections on 2026-11-11. Use a positive number: `-1` and `0` do not remove the inherited limit, neither with Docker Compose v2.32 (PROD) nor v5. Each thread costs memory (about 0.2 MB measured), so raise it together with the RAM of the VM.
- mongo_docker_max_conns - `--maxConns` of mongod, default `28000`, `0` disables it. With it mongod refuses the connections above the limit cleanly (it logs `Connection refused because there are too many open connections`, a good alert signature) instead of failing to create threads, and it keeps threads for its own replication and election work. The role fails if it is not at least 1000 below `mongo_limit_pids`, because mongod uses about 70 threads beyond the connections.
- mongo_docker_image - pinned in `group_vars/mongo_docker_servers.yml` to the version running on PROD. The role runs `docker-compose pull` before `up -d`, so a moving tag would upgrade mongod on the next deploy.

### Sizing of the connection limits

Measured on 2026-11-12 (nau-technical#1132): each LMS pod (`UWSGI_WORKERS=32`) holds about 1,825 connections to Mongo, about 600 per Mongo node.

| | Per Mongo node |
|---|---|
| 20 LMS pods (the HPA cap) | about 12k |
| plus workers and CMS | a few thousand |
| the primary carries about | +1.9k |
| a failover puts on the survivors about | 1.5x |
| realistic peak | about 20k |

`mongo_docker_max_conns` (28000) and `mongo_limit_pids` (32768) sit above that peak. Memory: about 0.2 MB per connection (upper bound 0.4 MB), so 28k connections cost about 6 GB on top of the WiredTiger cache (about 15.5 GB on a 32 GB node). Recompute both values if the LMS pod cap or `UWSGI_WORKERS` change, and for the load tests of nau-technical#1079.

Check the limits of a running node:
```bash
docker inspect mongo --format '{{.HostConfig.PidsLimit}}'
cat /sys/fs/cgroup/system.slice/docker-$(docker inspect mongo --format '{{.Id}}').scope/pids.{max,current}
docker exec mongo mongosh admin -u <admin> --eval 'db.serverStatus().connections'   # current / available
```
Do not run the `docker inspect ... {{.Id}}` command through an Ansible `-a` string, Ansible reads it as a template.

Apply a new thread limit to a running node without restarting it (the value survives reboots, but is lost when the container is recreated, so deploy the same value afterwards):
```bash
docker update --pids-limit 32768 mongo
```

### Deploying a change of `mongo_limit_pids`, `mongo_docker_max_conns` or the image

Changing them changes `docker-compose.yml`, so the deploy recreates the container (a restart of mongod). The mongo play runs `serial: 1` in inventory order, only with a `ping` healthcheck, so it does not wait for a node to be a caught-up SECONDARY, and it does not step the primary down. Do it by hand, node by node:

1. Try dev or stage first, and deploy off-peak.
2. Check the set and the lag. All members `health=1` and `lag_vs_primary` about 0:
   ```js
   // make mongo-shell
   var s = rs.status(); var p = s.members.find(m => m.stateStr == 'PRIMARY');
   s.members.map(m => `${m.name} ${m.stateStr} health=${m.health} lag_vs_primary=${(p.optimeDate - m.optimeDate)/1000}s`)
   ```
3. Dry run on one node. The only changes of `docker-compose.yml` must be `pids_limit` and `command` (and `image` if you changed it). `-e mongo_deploy=true` also runs `geerlingguy.docker` and `ansible-snmpd` on the node.
   ```bash
   ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit <host> -e mongo_deploy=true --check --diff
   ```
4. Secondaries first, one node at a time. For the primary, run `rs.stepDown(180, 15)` first, check with `make mongo-primary-node` that another node is primary, and only then deploy it.
   ```bash
   ansible-playbook -i nau-data/envs/<env>/hosts.ini deploy.yml --limit <host> -e mongo_deploy=true
   ```
5. Before the next node, run the replica set check of step 2 again, and check that the LMS has no new restarts and no Mongo errors.

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