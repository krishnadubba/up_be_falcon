import os
import logging
from conf import get_config
from confluent_kafka import Producer
from uggipuggi.models.recipe import ExposeLevel

# load config via env
#env = os.environ.get('UGGIPUGGI_BACKEND_ENV', 'docker_compose')
#config = get_config(env)
#kafka_bootstrap_servers = config['kafka'].get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
recipe_producer = Producer({'bootstrap.servers': kafka_bootstrap_servers})

def recipe_kafka_collection_post_producer(req, resp, resource):
    # Publish that a recipe has been added
    # Topic name is 'recipe' and partition is 'user_id'
    # Consumer reads pushes notifications to interested parties and feeds
    if req.params['body']['expose_level'] != ExposeLevel.PRIVATE:        
        parameters = [req.user_id, req.params['body']['user_name'], resp.body["recipe_id"], 
                      req.params['body']['recipe_name'], req.params['body']['images'][0], 
                      req.params['body']['expose_level'], resp.status]
        logging.debug("++++++++++++++++++++++")
        logging.debug("RECIPE_KAFKA_COLLECTION_POST_PRODUCER: %s" %req.kafka_topic_name)
        logging.debug("----------------------")
        logging.debug(repr(parameters))
        logging.debug("++++++++++++++++++++++")    
        recipe_producer.produce(topic=req.kafka_topic_name, 
                                value=repr(parameters),
                                key=req.user_id) #req.encode('utf-8'))
        recipe_producer.flush()
    
def recipe_kafka_item_get_producer(req, resp, resource):
    # This might be useful for number of views for recipe
    parameters = [req.user_id, resp.body["recipe_id"], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_ITEM_GET_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    recipe_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.params['body']['user_id']) #req.encode('utf-8'))
    recipe_producer.flush()
    
def recipe_kafka_item_put_producer(req, resp, resource):
    # Publish that a comment has been added to recipe
    if 'comment' in req.params['body']:
        parameters = [req.user_id, req.params['body']['comment']['user_name'], resp.recipe_author_id, 
                      resp.body["recipe_id"], req.params['body']['comment'], resp.status]
        logging.debug("++++++++++++++++++++++")
        logging.debug("RECIPE_KAFKA_ITEM_PUT_PRODUCER: %s" %req.kafka_topic_name)
        logging.debug("----------------------")
        logging.debug(repr(parameters))
        logging.debug("++++++++++++++++++++++")    
        recipe_producer.produce(topic=req.kafka_topic_name, 
                                value=repr(parameters),
                                key=req.user_id) #req.encode('utf-8'))
        recipe_producer.flush()
    
def recipe_kafka_item_delete_producer(req, resp, resource):
    parameters = [req.user_id, resp.body["recipe_id"], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_ITEM_DELETE_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    recipe_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.params['body']['user_id']) #req.encode('utf-8'))
    recipe_producer.flush()
    