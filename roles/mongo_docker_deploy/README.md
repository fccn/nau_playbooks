# Mongo docker deploy

Deploy Mongo DB service using a docker compose file.

This role deploys a Mongo DB service using `host` network.

Deploying a MongoDB Cluster with Docker
https://www.mongodb.com/compatibility/deploying-a-mongodb-cluster-with-docker

## Add Members to a Replica Set
https://www.mongodb.com/docs/v3.6/tutorial/expand-replica-set/

Deploy this role to new server.

Connect to the replica set’s primary. Run this to know which is the primary.
```
ssh pers...
mongo edxapp -u edxapp -pXXXXXXX -host rs0/localhost
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
mongo edxapp -u edxapp -pXXXXXXX -host rs0/localhost
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

https://www.mongodb.com/docs/manual/tutorial/expand-replica-set/


Upgrade a Replica Set to 4.0
https://www.mongodb.com/docs/manual/release-notes/4.0-upgrade-replica-set/
