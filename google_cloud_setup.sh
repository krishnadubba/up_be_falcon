#!/bin/bash
docker swarm init
docker network create -d overlay proxy
./build/generate_build_info.sh
docker build -t kr .
docker stack deploy -c google_cloud_setup.yml uggi
echo '======================================================'
echo 'For logs: docker service logs -f stackname_servicename'
echo 'Docker Overlay Network:'
docker network inspect docker_gwbridge --format '{{range $k, $v := index .IPAM.Config 0}}{{.| printf "%s: %s " $k}}{{end}}'
echo '======================================================'
