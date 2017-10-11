import logging
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
   
def user_kafka_item_get_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("USER_KAFKA_ITEM_GET_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def user_kafka_item_post_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("USER_KAFKA_ITEM_POST_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()