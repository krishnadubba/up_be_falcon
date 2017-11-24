import os
import logging
from conf import get_config
from confluent_kafka import Producer

kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
activity_kafka_producer = Producer({'bootstrap.servers': kafka_bootstrap_servers})     

def activity_kafka_collection_post_producer(req, resp, resource):
    if 'multipart/form-data' in req.content_type:
        parameters = [req.user_id, 
                      req.get_params("recipe_id"),
                      resp.body['images'],
                      resp.body["activity_id"], 
                      resp.status]
        logging.debug("++++++++++++++++++++++")
        logging.debug("ACTIVITY_KAFKA_COLLECTION_POST_PRODUCER: %s" %req.kafka_topic_name)
        logging.debug("----------------------")
        logging.debug(repr(parameters))
        logging.debug("++++++++++++++++++++++")    
        activity_kafka_producer.produce(topic=req.kafka_topic_name, 
                                        value=repr(parameters),
                                        key=req.user_id) #req.encode('utf-8'))
        activity_kafka_producer.flush()
        
def activity_kafka_item_get_producer(req, resp, resource):
    parameters = [req.user_id, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("ACTIVITY_KAFKA_ITEM_GET_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    activity_kafka_producer.produce(topic=req.kafka_topic_name, 
                                    value=repr(parameters),
                                    key=req.user_id) #req.encode('utf-8'))
    activity_kafka_producer.flush()
    
def activity_kafka_item_put_producer(req, resp, resource):
    if 'comment' in req.body:
        parameters = [req.user_id, resp.activity_author_id, resp.status]
        logging.debug("++++++++++++++++++++++")
        logging.debug("ACTIVITY_KAFKA_ITEM_PUT_PRODUCER: %s" %req.kafka_topic_name)
        logging.debug("----------------------")
        logging.debug(repr(parameters))
        logging.debug("++++++++++++++++++++++")    
        activity_kafka_producer.produce(topic=req.kafka_topic_name, 
                                        value=repr(parameters),
                                        key=req.user_id) #req.encode('utf-8'))
        activity_kafka_producer.flush()
    
def activity_kafka_item_delete_producer(req, resp, resource):
    parameters = [req.user_id, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("ACTIVITY_KAFKA_ITEM_DELETE_PRODUCER: %s" %req.kafka_topic_name)
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    activity_kafka_producer.produce(topic=req.kafka_topic_name, 
                                    value=repr(parameters),
                                    key=req.user_id) #req.encode('utf-8'))
    activity_kafka_producer.flush()
    