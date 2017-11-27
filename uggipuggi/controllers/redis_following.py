# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging
from bson import json_util, ObjectId
from uggipuggi.constants import FOLLOWERS, FOLLOWING, USER
from uggipuggi.services.user import get_user  
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.messaging.following_kafka_producers import following_kafka_item_post_producer,\
                                                          following_kafka_item_put_producer


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'following_item'

    @falcon.before(deserialize)
    #@falcon.after(group_kafka_item_get_producer)
    def on_get(self, req, resp, id):
        # Get all following of user
        if id != req.user_id:
            resp.status = falcon.HTTP_UNAUTHORIZED
        else:    
            req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
            user_following_list = FOLLOWING + id
            resp.body = req.redis_conn.smembers(user_following_list)
            resp.status = falcon.HTTP_FOUND
        
    @falcon.before(deserialize)
    @falcon.after(following_kafka_item_post_producer)
    def on_post(self, req, resp, id):
        if id != req.user_id:
            resp.status = falcon.HTTP_UNAUTHORIZED
        else:    
            req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
            logger.debug("Deleting member from user following in database ...")
            #following_id_name = FOLLOWING + id
            if 'public_user_id' in req.params['body']:
                # req.params['body']['public_user_id'] is a LIST
                user_following_list = FOLLOWING + id
                public_user_id = req.params['body']['public_user_id']
                req.redis_conn.srem(user_following_list, *public_user_id)
                # Update the count of following number in the concise view
                req.redis_conn.hmset(USER + id, 
                                    {'num_following':req.redis_conn.scard(user_following_list)})
                
                logger.debug("Deleted member from user following list in database")
                
                pipeline = req.redis_conn.pipeline(True)
                for followee in public_user_id:
                    public_user_followers_list = FOLLOWERS + followee
                    pipeline.srem(public_user_followers_list, id)
                    logger.debug("Removed user to public user's followers list in database")                            
                pipeline.execute()
                
                # Change the number of followers of the followee in concise user view
                for followee in public_user_id:
                    public_user_followers_list = FOLLOWERS + followee
                    # Update the count of followers number in the concise view
                    req.redis_conn.hmset(USER + followee, 
                                     {'num_followers':req.redis_conn.scard(public_user_followers_list)})                

                resp.status = falcon.HTTP_OK
            else:
                logger.warn("Please provide public_user_id to delete from users following list")
                resp.status = falcon.HTTP_BAD_REQUEST
                raise falcon.HTTPMissingParam('public_user_id')

    @falcon.before(deserialize)
    @falcon.after(following_kafka_item_put_producer)
    def on_put(self, req, resp, id):
        # No need for authorization, anyone can follow anyone
        # We need to call this when user follows someone
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
            
        logger.debug("Adding member to user following list in database ... %s" %repr(id))
        if 'public_user_id' in req.params['body']:
            public_user_id = req.params['body']['public_user_id']
            public_user = get_user('id', public_user_id)
            # If user profile is not public, no followers
            if not public_user.public_profile:
                logger.warn("Cannot follow this user as the profile is not public")
                resp.status = falcon.HTTP_FORBIDDEN
                description = ('Cannot follow this user as the profile is not public')
                raise falcon.HTTPForbidden('Cannot follow this user as the profile is not public',
                                           description
                                           )            
            user_following_list = FOLLOWING + id        
            # Add celebrity to user's following list
            req.redis_conn.sadd(user_following_list, public_user_id)
            # Update the count of following number in the concise view
            req.redis_conn.hmset(USER + id, 
                                 {'num_following':req.redis_conn.scard(user_following_list)}) 
            
            logger.debug("Added member to user following list in database")
            
            # Add user to public user (celebrity) followers list
            public_user_followers_list = FOLLOWERS + public_user_id
            req.redis_conn.sadd(public_user_followers_list, id)
            
            # Change the number of followers of the followee in concise user view
            req.redis_conn.hmset(USER + public_user_id, 
                                 {'num_followers':req.redis_conn.scard(public_user_followers_list)})
            
            logger.debug("Added user to following followers in database")            
            resp.status = falcon.HTTP_OK
        else:
            logger.warn("Please provide public_user_id to add to users following")
            resp.status = falcon.HTTP_BAD_REQUEST
            raise falcon.HTTPMissingParam('public_user_id')
