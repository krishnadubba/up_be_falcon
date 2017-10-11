import logging
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'

def kafka_verify_post_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_VERIFY_POST_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def kafka_register_post_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_REGISTER_POST_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def kafka_login_post_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_LOGIN_POST_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    
def kafka_forgotpassword_post_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_FORGOTPASSWORD_POST_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")    
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
def kafka_passwordchange_post_producer(req, resp, resource):
    parameters = [req.kafka_topic_name, req.body, resp, resource]
    logging.debug("++++++++++++++++++++++")
    logging.debug("KAFKA_PASSWORDCHANGE_POST_PRODUCER")
    logging.debug("++++++++++++++++++++++")
    logging.debug(repr(parameters))
    logging.debug("++++++++++++++++++++++")
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    p.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    p.flush()
    