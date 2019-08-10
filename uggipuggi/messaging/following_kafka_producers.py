import os
from conf import get_config
from confluent_kafka import Producer

from uggipuggi.helpers.logs_metrics import init_logger


logger = init_logger()
# load config via env
kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
following_producer = Producer({'bootstrap.servers': kafka_bootstrap_servers})

def following_kafka_item_get_producer(req, resp, resource):
    # This might be useful for number of views for recipe
    parameters = [req.user_id, resp.status]
    logger.debug("++++++++++++++++++++++")
    logger.debug("FOLLOWING_KAFKA_ITEM_GET_PRODUCER: %s" %req.kafka_topic_name)
    logger.debug("----------------------")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    following_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    following_producer.flush()

def following_kafka_item_put_producer(req, resp, resource):
    # Recipe updated, night not be useful
    parameters = [req.user_id, req.params['body']['public_user_id'], resp.status]
    logger.debug("++++++++++++++++++++++")
    logger.debug("FOLLOWING_KAFKA_ITEM_PUT_PRODUCER: %s" %req.kafka_topic_name)
    logger.debug("----------------------")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    following_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    following_producer.flush()
        
def following_kafka_item_post_producer(req, resp, resource):
    parameters = [req.user_id, resp.status]
    logger.debug("++++++++++++++++++++++")
    logger.debug("FOLLOWING_KAFKA_ITEM_POST_PRODUCER: %s" %req.kafka_topic_name)
    logger.debug("----------------------")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")
    following_producer.produce(topic=req.kafka_topic_name, 
                            value=repr(parameters),
                            key=req.user_id) #req.encode('utf-8'))
    following_producer.flush()
    