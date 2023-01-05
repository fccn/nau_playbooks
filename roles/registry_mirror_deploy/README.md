# Ansible role to deploy docker registry mirror

Deploy a docker hub registry mirror, so we aren't limited to Docker Hub rate limit and have better
performance on download images.

## Deploy
```bash
docker-compose up
```

## Configure docker daemon
```bash
cat /etc/docker/daemon.json
```

Content should include:

```json
{
  "registry-mirrors": ["http://localhost:5000"],
  "insecure-registries": ["localhost:5000"]
}
```

# Test
```bash
docker image rm ubuntu:latest
docker pull ubuntu:latest
```

# Logs
Docker daemon logs

```bash
journalctl -u docker.service
```