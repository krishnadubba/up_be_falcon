import os
import logging
from conf import get_config
from confluent_kafka import Producer

# load config via env
kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
group_producer = Producer({'bootstrap.servers': kafka_bootstrap_servers})

def group_kafka_collection_post_producer(req, resp, resource):
    # Topic name is 'recipe' and partition is 'user_id'
    # Consumer reads pushes notifications to interested parties and feeds
    parameters = [req.user_id, resp.body["group_id"], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("GROUP_KAFKA_COLLECTION_POST_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    group_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    group_producer.flush()
    
def group_kafka_collection_delete_producer(req, resp, resource):
    # Topic name is 'recipe' and partition is 'user_id'
    # Consumer reads pushes notifications to interested parties and feeds
    parameters = [req.user_id, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("GROUP_KAFKA_COLLECTION_DELETE_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    group_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    group_producer.flush()
    
def group_kafka_item_get_producer(req, resp, resource):
    # This might be useful for number of views for recipe
    parameters = [req.user_id, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("GROUP_KAFKA_ITEM_GET_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    group_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    group_producer.flush()
    
def group_kafka_item_put_producer(req, resp, resource):
    # Recipe updated, night not be useful
    parameters = [req.user_id, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("GROUP_KAFKA_ITEM_PUT_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    group_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    group_producer.flush()

def group_kafka_item_post_producer(req, resp, resource):
    # Recipe updated, night not be useful
    parameters = [req.user_id, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("GROUP_KAFKA_ITEM_POST_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    group_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    group_producer.flush()
        
def group_kafka_item_delete_producer(req, resp, resource):
    parameters = [req.user_id, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("GROUP_KAFKA_ITEM_DELETE_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    group_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    group_producer.flush()
    