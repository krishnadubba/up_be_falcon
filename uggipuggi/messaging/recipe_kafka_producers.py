import logging
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
recipe_producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

def recipe_kafka_collection_post_producer(req, resp, resource):
    # Topic name is 'recipe' and partition is 'user_id'
    # Consumer reads pushes notifications to interested parties and feeds
    parameters = [req.body['user_id'], resp.body["recipe_id"], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_COLLECTION_POST_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    recipe_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.body['user_id']) #req.encode('utf-8'))
    recipe_producer.flush()
    
def recipe_kafka_item_get_producer(req, resp, resource):
    # This might be useful for number of views for recipe
    parameters = [req.body['user_id'], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_ITEM_GET_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    recipe_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.body['user_id']) #req.encode('utf-8'))
    recipe_producer.flush()
    
def recipe_kafka_item_put_producer(req, resp, resource):
    # Recipe updated, night not be useful
    parameters = [req.body['user_id'], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_ITEM_PUT_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    recipe_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.body['user_id']) #req.encode('utf-8'))
    recipe_producer.flush()
    
def recipe_kafka_item_delete_producer(req, resp, resource):
    parameters = [req.body['user_id'], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("RECIPE_KAFKA_ITEM_DELETE_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    recipe_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.body['user_id']) #req.encode('utf-8'))
    recipe_producer.flush()
    