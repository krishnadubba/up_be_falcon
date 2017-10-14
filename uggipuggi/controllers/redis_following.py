# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging
from bson import json_util, ObjectId
from uggipuggi import constants
from uggipuggi.controllers.hooks import deserialize, serialize, read_req_body, supply_redis_conn
from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.messaging.following_kafka_producers import following_kafka_item_post_producer,\
                                                          following_kafka_item_delete_producer


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'following_item'

    @falcon.before(read_req_body)
    @falcon.after(serialize)
    #@falcon.after(group_kafka_item_get_producer)
    def on_get(self, req, resp, id):
        # Get all following of user
        if id != req.user_id:
            resp.status = falcon.HTTP_UNAUTHORIZED
        else:    
            req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
            following_id_name = 'following:' + id
            resp.body = req.redis_conn.smembers(following_id_name)
            resp.status = falcon.HTTP_FOUND
        
    @falcon.before(read_req_body)    
    @falcon.after(serialize)
    @falcon.after(following_kafka_item_delete_producer)
    def on_delete(self, req, resp, id):
        if id != req.user_id:
            resp.status = falcon.HTTP_UNAUTHORIZED
        else:    
            req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
            logger.debug("Deleting member from user following in database ...")
            following_id_name = 'following:' + id
            if 'following_user_id' in req.body:
                req.redis_conn.sdel(following_id_name, req.body['following_user_id'])
                logger.debug("Deleted member from user following in database")
                
                followers_id_name = 'followers:' + req.body['follower_user_id']
                req.redis_conn.sdel(followers_id_name, id)
                logger.debug("Added user to following followers in database")                            
                resp.status = falcon.HTTP_OK
            else:
                logger.warn("Please provide following_user_id to delete from users following list")
                resp.status = falcon.HTTPMissingParam                

    @falcon.before(read_req_body)
    @falcon.after(serialize)
    @falcon.after(following_kafka_item_post_producer)
    def on_post(self, req, resp, id):
        # No need for authorization, anyone can follow anyone
        # We need to call this when user follows someone
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        logger.debug("Adding member to user following in database ... %s" %repr(id))
        following_id_name = 'following:' + id        
        if 'follower_user_id' in req.body:
            # Add celebrity to user's following list
            req.redis_conn.sadd(following_id_name, req.body['follower_user_id'])
            logger.debug("Added member to user following in database")
            
            # Add user to celebrity followers list
            followers_id_name = 'followers:' + req.body['follower_user_id']
            req.redis_conn.sadd(followers_id_name, id)
            logger.debug("Added user to following followers in database")            
            resp.status = falcon.HTTP_OK
        else:
            logger.warn("Please provide contact_user_id to add to users following")
            resp.status = falcon.HTTPMissingParam
            