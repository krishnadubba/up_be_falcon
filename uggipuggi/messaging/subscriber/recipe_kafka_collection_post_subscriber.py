"""
To stop workers, you can use the kill command. We can query for the process id and then 
eliminate the workers based on this information.

ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill

This will allow the worker to complete its current task before exiting.
If you wish to shut down all workers without waiting for them to complete their tasks:

ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill -9

"""

import os, sys
from bson import json_util
from confluent_kafka import Consumer, KafkaError

sys.path.append('/home/dubba/work/webdev/backends/up_be_falcon')
from uggipuggi.tasks.recipe_add_task import user_feed_add_recipe


KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
c = Consumer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS, 'group.id': 'mygroup',
              'default.topic.config': {'auto.offset.reset': 'smallest'}})
c.subscribe(['recipe_collection_post'])
running = True	

while running:
    try:
        msg = c.poll(timeout=1.0)
        if msg is not None:
            if not msg.error():
                print('Received message: %s' % msg.value().decode('utf-8'))
                user_feed_add_recipe.delay(msg.value().decode('utf-8'))
            elif msg.error().code() != KafkaError._PARTITION_EOF:
                print(msg.error())
                running = False
            
    except KeyboardInterrupt:
        # quit
        c.close()
        sys.exit()
            

