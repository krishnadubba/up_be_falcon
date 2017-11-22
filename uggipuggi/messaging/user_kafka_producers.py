import os
import logging
from conf import get_config
from confluent_kafka import Producer

# load config via env
kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
   
def user_kafka_item_get_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.params['query'], resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("USER_KAFKA_ITEM_GET_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': kafka_bootstrap_servers})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def user_kafka_item_put_producer(req, resp, resource):
    if 'multipart/form-data' in req.content_type:
        parameters = [req.kafka_topic_name, req._params.keys(), resp, resource]
    else:    
        parameters = [req.kafka_topic_name, req.params['body'].keys(), resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("USER_KAFKA_ITEM_PUT_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': kafka_bootstrap_servers})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()