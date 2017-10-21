"""
To stop workers, you can use the kill command. We can query for the process id and then 
eliminate the workers based on this information.

ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill

This will allow the worker to complete its current task before exiting.
If you wish to shut down all workers without waiting for them to complete their tasks:

ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill -9

"""

import os, sys
import logging
from bson import json_util
from confluent_kafka import Consumer, KafkaError

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(sys.path[0])))
sys.path.append(ROOT_DIR)
from conf import get_config
from uggipuggi.tasks.recipe_add_task import user_feed_add_recipe

# load config via env
env = os.environ.get('UGGIPUGGI_BACKEND_ENV', 'docker_compose')
config = get_config(env)
kafka_bootstrap_servers = config['kafka'].get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

logging.debug("=====================================================")
logging.debug("KAFKA_BOOTSTRAP_SERVERS: %s" %kafka_bootstrap_servers)
logging.debug("=====================================================")

c = Consumer({'bootstrap.servers': kafka_bootstrap_servers, 'group.id': 'mygroup',
              'default.topic.config': {'auto.offset.reset': 'smallest'}})
c.subscribe(['recipe_collection_post'])

running = True	
try:
    while running:
        msg = c.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            # Error or event
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event
                logging.error('%% %s [%d] reached end at offset %d\n' %
                              (msg.topic(), msg.partition(), msg.offset()))
            elif msg.error():
                # Error
                raise KafkaException(msg.error())
        else:
            logging.debug('Received message: %s' % msg.value().decode('utf-8'))
            user_feed_add_recipe.delay(msg.value().decode('utf-8'))
            
except KeyboardInterrupt:
    logging.error('%% Aborted by user\n')
    
    # quit
c.close()
            

