#!/bin/bash
docker swarm init
docker build -t kr .
docker stack deploy -c localsetup.yml uggi
