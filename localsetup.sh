#!/bin/bash
docker swarm init
docker network create -d overlay proxy
docker build -t kr .
docker stack deploy -c localsetup.yml uggi
DOCKER_GWBRIDGE_IP=`ifconfig docker_gwbridge | awk '/inet addr/ {gsub("addr:", "", $2); print $2}'`
xdg-open http://$DOCKER_GWBRIDGE_IP/test
xdg-open http://$DOCKER_GWBRIDGE_IP/visualizer
echo '======================================================'
echo 'For logs: docker service logs -f stackname_servicename'
echo 'Docker Overlay Network:'
docker network inspect docker_gwbridge --format '{{range $k, $v := index .IPAM.Config 0}}{{.| printf "%s: %s " $k}}{{end}}'
echo '======================================================'
