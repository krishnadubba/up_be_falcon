#!/bin/bash
docker swarm init --advertise-addr 192.168.1.69
docker network create -d overlay proxy
./build/generate_build_info.sh
docker build -t kr .
docker build -t up_fluentd ./fluentd
docker build -t up_statsd_agent ./statsd_agent
docker stack deploy -c localsetup.yml uggi
DOCKER_GWBRIDGE_IP=`ifconfig docker_gwbridge | awk '/inet / {gsub("", "", $2); print $2}'`
xdg-open http://$DOCKER_GWBRIDGE_IP/ping
xdg-open http://$DOCKER_GWBRIDGE_IP/visualizer
echo '======================================================'
echo 'For logs: docker service logs -f stackname_servicename'
echo 'Docker Overlay Network:'
docker network inspect docker_gwbridge --format '{{range $k, $v := index .IPAM.Config 0}}{{.| printf "%s: %s " $k}}{{end}}'
echo '======================================================'
