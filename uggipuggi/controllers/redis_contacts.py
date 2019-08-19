# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging
from bson import json_util, ObjectId
from uggipuggi.constants import CONTACTS
from uggipuggi.services.user import get_user
from uggipuggi.helpers.logs_metrics import init_logger, init_statsd
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.messaging.contacts_kafka_producers import contacts_kafka_item_post_producer,\
                                                         contacts_kafka_item_put_producer


logger = init_logger()
statsd = init_statsd('up.controllers.contacts')

@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'contacts_item'

    @falcon.before(deserialize)
    #@falcon.after(contacts_kafka_item_get_producer)
    @statsd.timer('get_contacts_get')
    def on_get(self, req, resp, id):
        # Get all contacts of user
        if id != req.user_id:
            resp.status = falcon.HTTP_UNAUTHORIZED
        else:    
            req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
            contacts_id_name = CONTACTS + id
            resp.body = req.redis_conn.smembers(contacts_id_name)
            resp.status = falcon.HTTP_OK
        
    @falcon.before(deserialize)
    @falcon.after(contacts_kafka_item_post_producer)
    @statsd.timer('delete_contacts_post')
    def on_post(self, req, resp, id):
        if id != req.user_id:
            resp.status = falcon.HTTP_UNAUTHORIZED
        else:    
            req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
            logger.debug("Deleting member from user contacts in database ...")
            contacts_id_name = CONTACTS + id
            try:
                # req.params['body']['contact_user_id'] is a list
                req.redis_conn.srem(contacts_id_name, *req.params['body']['contact_user_id'])
                logger.debug("Deleted member from user contacts in database")
                resp.status = falcon.HTTP_OK
                statsd.incr('delete_contact.invocations')
            except KeyError:
                logger.warn("Please provide contact_user_id to delete from users contact")
                resp.status = falcon.HTTP_BAD_REQUEST
                raise falcon.HTTPMissingParam('contact_user_id')

    @falcon.before(deserialize)
    @falcon.after(contacts_kafka_item_put_producer)
    @statsd.timer('add_contacts_put')
    def on_put(self, req, resp, id):
        # Note that, here we get contacts phone numbers, not their user_ids
        if id != req.user_id:
            resp.status = falcon.HTTP_UNAUTHORIZED
        else:
            logger.debug("Adding member to user contacts in database ... %s" %repr(id))
            if 'contact_user_id' in req.params['body'] and len(req.params['body']['contact_user_id']) > 0:
                req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
                contacts_id_list = CONTACTS + id
                # req.params['body']['contact_user_id'] is a LIST of contact phone numbers
                # So first get user_ids for these phone numbers
                contact_user_ids = req.redis_conn.mget(req.params['body']['contact_user_id'])
                # Only add non_none contact ids
                req.redis_conn.sadd(contacts_id_list, *[i for i in contact_user_ids if i])
                logger.debug("Added member to user contacts in database: %s"  %repr(req.params['body']['contact_user_id']))
                resp.status = falcon.HTTP_OK
                resp.body = contact_user_ids
                statsd.incr('add_contact.invocations')
            else:
                logger.warn("Please provide contact_user_id to add to users contacts")
                resp.status = falcon.HTTP_BAD_REQUEST
                raise falcon.HTTPMissingParam('contact_user_id')