from __future__ import absolute_import
import time
import falcon
import logging
from bson import json_util, ObjectId
from uggipuggi.constants import FOLLOWERS, USER
from uggipuggi.helpers.logs_metrics import init_logger, init_statsd
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.messaging.followers_kafka_producers import followers_kafka_item_post_producer


logger = init_logger()
statsd = init_statsd('up.controllers.followers')

@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'followers_item'

    @falcon.before(deserialize)
    #@falcon.after(group_kafka_item_get_producer)
    @statsd.timer('get_followers_get')
    def on_get(self, req, resp, id):
        # Get all followers of user
        statsd.incr('get_followers.invocations')
        if id != req.user_id:
            resp.status = falcon.HTTP_UNAUTHORIZED
        else:    
            req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
            followers_list = FOLLOWERS + id
            resp.body = req.redis_conn.smembers(followers_list)
            resp.status = falcon.HTTP_OK            
        
    @falcon.before(deserialize)    
    @falcon.after(followers_kafka_item_post_producer)
    @statsd.timer('delete_followers_post')
    def on_post(self, req, resp, id):
        # Delete a member from followers list. Note there is no "add" member to 
        # followers list as you can't make somebody follow you by yourself 
        statsd.incr('delete_follower.invocations')
        if id != req.user_id:
            resp.status = falcon.HTTP_UNAUTHORIZED
        else:    
            req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
            logger.debug("Deleting member from user followers in database ...")
            followers_list = FOLLOWERS + id
            try:
                # req.params['body']['follower_user_id'] is a list
                req.redis_conn.srem(followers_list, *req.params['body']['follower_user_id'])
                
                # Change the number of followers of the followee in concise user view
                req.redis_conn.hmset(USER + id, {'num_followers':req.redis_conn.scard(followers_list)})
                
                logger.debug("Deleted member from user followers in database")
                resp.status = falcon.HTTP_OK                
            except KeyError:
                logger.warn("Please provide follower_user_id to delete from users contact")
                resp.status = falcon.HTTP_BAD_REQUEST
                raise falcon.HTTPMissingParam('follower_user_id')