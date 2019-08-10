import os
from conf import get_config
from confluent_kafka import Producer

from uggipuggi.helpers.logs_metrics import init_logger

# load config via env
kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
logger = init_logger()   
   
def user_kafka_item_get_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.params['query'], resp, resource]
    logger.debug("++++++++++++++++++++++")
    logger.debug("USER_KAFKA_ITEM_GET_PRODUCER")
    logger.debug("++++++++++++++++++++++")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': kafka_bootstrap_servers})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def user_kafka_item_put_producer(req, resp, resource):
    if 'multipart/form-data' in req.content_type:
        parameters = [req.kafka_topic_name, req._params.keys(), resp, resource]
    else:    
        parameters = [req.kafka_topic_name, req.params['body'].keys(), resp, resource]
    logger.debug("++++++++++++++++++++++")
    logger.debug("USER_KAFKA_ITEM_PUT_PRODUCER")
    logger.debug("++++++++++++++++++++++")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': kafka_bootstrap_servers})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def user_recipes_kafka_item_get_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.user_id, resource]
    logger.debug("++++++++++++++++++++++")
    logger.debug("USER_RECIPES_KAFKA_ITEM_GET_PRODUCER")
    logger.debug("++++++++++++++++++++++")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': kafka_bootstrap_servers})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def user_saved_kafka_item_get_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.user_id, resource]
    logger.debug("++++++++++++++++++++++")
    logger.debug("USER_SAVED_KAFKA_ITEM_GET_PRODUCER")
    logger.debug("++++++++++++++++++++++")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': kafka_bootstrap_servers})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def user_activity_kafka_item_get_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.user_id, resource]
    logger.debug("++++++++++++++++++++++")
    logger.debug("USER_ACTIVITY_KAFKA_ITEM_GET_PRODUCER")
    logger.debug("++++++++++++++++++++++")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': kafka_bootstrap_servers})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()    