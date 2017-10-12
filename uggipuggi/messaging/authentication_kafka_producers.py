import logging
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
authentication_kafka_producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

def kafka_verify_post_producer(req, resp, resource):
    parameters = [req.user_id, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_VERIFY_POST_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
    
def kafka_register_post_producer(req, resp, resource):
    parameters = [req.body['phone'], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_REGISTER_POST_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
    
def kafka_login_post_producer(req, resp, resource):
    parameters = [req.body["email"], resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_LOGIN_POST_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
    
def kafka_forgotpassword_post_producer(req, resp, resource):
    parameters = [req.body, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_FORGOTPASSWORD_POST_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
def kafka_passwordchange_post_producer(req, resp, resource):
    parameters = [req.body, resp.status]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_PASSWORDCHANGE_POST_PRODUCER")
    logging.debug("----------------------")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
    