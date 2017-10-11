import logging
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'

def recipe_kafka_collection_post_producer(req, resp, resource):
    # Topic name is 'recipe' and partition is 'user_id'
    # Consumer reads pushes notifications to interested parties and feeds
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_COLLECTION_POST_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def recipe_kafka_item_get_producer(req, resp, resource):
    # This might be useful for number of views for recipe
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_ITEM_GET_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def recipe_kafka_item_post_producer(req, resp, resource):
    # Recipe updated, night not be useful
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_ITEM_POST_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def recipe_kafka_item_delete_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_ITEM_DELETE_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    