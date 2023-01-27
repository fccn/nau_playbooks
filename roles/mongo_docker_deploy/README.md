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
mongo admin -u admin -pXXXXXXX -host rs0/localhost
db.hello()
```

Add this new mongo to the replica set.
```
rs.add( { host: "<new VM>:27017", priority: 0, votes: 0 } )
```

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
cfg.members[4].priority = 1
cfg.members[4].votes = 1
rs.reconfig(cfg)
```

https://www.mongodb.com/docs/manual/tutorial/expand-replica-set/


Upgrade a Replica Set to 4.0
https://www.mongodb.com/docs/manual/release-notes/4.0-upgrade-replica-set/
