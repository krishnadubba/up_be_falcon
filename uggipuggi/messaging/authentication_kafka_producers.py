import os
from conf import get_config
from confluent_kafka import Producer

from uggipuggi.helpers.logs_metrics import init_logger

kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
authentication_kafka_producer = Producer({'bootstrap.servers': kafka_bootstrap_servers})

logger = init_logger()

def kafka_verify_producer(req, resp, resource):
    parameters = [req.user_id, resp.status]
    logger.debug("++++++++++++++++++++++")
    logger.debug("KAFKA_VERIFY_PRODUCER: %s" %req.kafka_topic_name)
    logger.debug("----------------------")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
    
def kafka_register_producer(req, resp, resource):
    parameters = [req.params['body']['phone'], resp.status]
    logger.debug("++++++++++++++++++++++")
    logger.debug("KAFKA_REGISTER_PRODUCER: %s" %req.kafka_topic_name)
    logger.debug("----------------------")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
    
def kafka_login_producer(req, resp, resource):
    parameters = [req.params['body']["email"], resp.status]
    logger.debug("++++++++++++++++++++++")
    logger.debug("KAFKA_LOGIN_PRODUCER: %s" %req.kafka_topic_name)
    logger.debug("----------------------")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
    
def kafka_logout_producer(req, resp, resource):
    parameters = [req.params['body']["email"], resp.status]
    logger.debug("++++++++++++++++++++++")
    logger.debug("KAFKA_LOGOUT_PRODUCER: %s" %req.kafka_topic_name)
    logger.debug("----------------------")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
    
def kafka_forgotpassword_producer(req, resp, resource):
    parameters = [req.params['body'], resp.status]
    logger.debug("++++++++++++++++++++++")
    logger.debug("KAFKA_FORGOTPASSWORD_PRODUCER: %s" %req.kafka_topic_name)
    logger.debug("----------------------")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")    
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
def kafka_passwordchange_producer(req, resp, resource):
    parameters = [req.params['body'], resp.status]
    logger.debug("++++++++++++++++++++++")
    logger.debug("KAFKA_PASSWORDCHANGE_PRODUCER: %s" %req.kafka_topic_name)
    logger.debug("----------------------")
    logger.debug(repr(parameters))
    logger.debug("++++++++++++++++++++++")
    authentication_kafka_producer.produce(req.kafka_topic_name, repr(parameters)) #req.encode('utf-8'))
    authentication_kafka_producer.flush()
    