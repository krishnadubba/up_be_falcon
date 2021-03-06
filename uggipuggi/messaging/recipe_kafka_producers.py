import os
import logging
from conf import get_config
from confluent_kafka import Producer
from uggipuggi.models import ExposeLevel

kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
recipe_producer = Producer({'bootstrap.servers': kafka_bootstrap_servers})

def recipe_kafka_collection_post_producer(req, resp, resource):
    # Publish that a recipe has been added
    # Topic name is 'recipe' and partition is 'user_id'
    # Consumer reads pushes notifications to interested parties and feeds
    if 'multipart/form-data' in req.content_type and req.get_param('expose_level') != ExposeLevel.PRIVATE:
        parameters = [req.user_id, 
                      req.get_param('expose_level'), 
                      resp.body['recipe_id'],
                      resp.status]
        try:
            parameters.append(resp.body['images'])
        except KeyError:
            parameters.append([])
            
        logging.debug("++++++++++++++++++++++")
        logging.debug("RECIPE_KAFKA_COLLECTION_POST_PRODUCER: %s" %req.kafka_topic_name)
        logging.debug(req.get_param('expose_level'))
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
                            key=req.user_id) #req.encode('utf-8'))
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
                            key=req.user_id) #req.encode('utf-8'))
    recipe_producer.flush()
    
def recipe_saved_kafka_item_post_producer(req, resp, resource):    
    parameters = [req.user_id, resp.body["recipe_id"], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_SAVED_KAFKA_ITEM_POST_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    recipe_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    recipe_producer.flush()

def recipe_liked_kafka_item_post_producer(req, resp, resource):    
    parameters = [req.user_id, resp.body["recipe_id"], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_LIKED_KAFKA_ITEM_POST_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    recipe_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    recipe_producer.flush()    