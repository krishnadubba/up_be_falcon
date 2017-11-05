#!/bin/bash
docker swarm init
docker build -t kr .
docker stack deploy -c localsetup.yml uggi
xdg-open http://172.17.0.1/test
xdg-open http://172.17.0.1/visualizer
echo '======================================================'
echo 'For logs: docker service logs -f stackname_servicename'
echo '======================================================'
