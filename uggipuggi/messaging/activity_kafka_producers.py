import logging
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
activity_kafka_producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})     

def activity_kafka_collection_post_producer(req, resp, resource):
    parameters = [req.body['user_id'], resp.body["activity_id"], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("ACTIVITY_KAFKA_COLLECTION_POST_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    activity_kafka_producer.produce(topic=req.kafka_topic_name, 
                                    value=repr(parameters),
                                    key=req.body['user_id']) #req.encode('utf-8'))
    activity_kafka_producer.flush()
    
def activity_kafka_item_get_producer(req, resp, resource):
    parameters = [req.body['user_id'], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("ACTIVITY_KAFKA_ITEM_GET_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    activity_kafka_producer.produce(topic=req.kafka_topic_name, 
                                    value=repr(parameters),
                                    key=req.body['user_id']) #req.encode('utf-8'))
    activity_kafka_producer.flush()
    
def activity_kafka_item_put_producer(req, resp, resource):
    parameters = [req.body['user_id'], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("ACTIVITY_KAFKA_ITEM_PUT_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    activity_kafka_producer.produce(topic=req.kafka_topic_name, 
                                    value=repr(parameters),
                                    key=req.body['user_id']) #req.encode('utf-8'))
    activity_kafka_producer.flush()
    
def activity_kafka_item_delete_producer(req, resp, resource):
    parameters = [req.body['user_id'], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("ACTIVITY_KAFKA_ITEM_DELETE_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    activity_kafka_producer.produce(topic=req.kafka_topic_name, 
                                    value=repr(parameters),
                                    key=req.body['user_id']) #req.encode('utf-8'))
    activity_kafka_producer.flush()
    