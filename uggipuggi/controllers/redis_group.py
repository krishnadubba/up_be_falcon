# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging
from bson import json_util, ObjectId
from uggipuggi.constants import GROUP, GROUP_MEMBERS, USER_GROUPS
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.messaging.group_kafka_producers import group_kafka_item_put_producer, group_kafka_item_post_producer,\
       group_kafka_item_delete_producer, group_kafka_collection_post_producer, group_kafka_collection_delete_producer 


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Collection(object):
    def __init__(self):
        self.kafka_topic_name = 'group_collection'

    @falcon.before(deserialize)
    def on_get(self, req, resp):
        # Get all groups of user
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        user_groups_id = USER_GROUPS + req.user_id
        resp.body['user_groups'] = list(req.redis_conn.smembers(user_groups_id))
        resp.status = falcon.HTTP_FOUND
        
    #@falcon.before(deserialize_create)
    @falcon.before(deserialize)
    @falcon.after(group_kafka_collection_post_producer)
    def on_post(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        # Get new group ID
        group_id = str(req.redis_conn.incr(GROUP))
        logger.debug('New group id created: %s' %group_id)
        group_id_name = GROUP + group_id
        user_groups_id = USER_GROUPS + req.user_id
        group_members_id_name = GROUP_MEMBERS + group_id
        
        pipeline = req.redis_conn.pipeline(True)        
        pipeline.hmset(group_id_name, {
            'group_name': req.params['body']['group_name'],
            'group_pic' : req.params['body']['group_pic'],
            'created_time': time.time(),
            'admin'       : req.user_id
        })
        
        # Add admin (current user) to group_members        
        pipeline.sadd(group_members_id_name, req.user_id)
        
        # Add this group to set of groups a user belongs to        
        pipeline.sadd(user_groups_id, group_id_name)
        pipeline.execute()
        resp.body = {"group_id": group_id}
        resp.status = falcon.HTTP_CREATED
        
    @falcon.before(deserialize)
    @falcon.after(group_kafka_collection_delete_producer)
    def on_delete(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Deleting group data in database ...")
        group_id_name = GROUP + req.params['query']['group_id']
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = falcon.HTTP_UNAUTHORIZED
            return
        else:
            group_members_id_name = GROUP_MEMBERS + group_id
            pipeline = req.redis_conn.pipeline(True)
            group_keys = list(req.redis_conn.hgetall(group_id_name).keys())
            req.redis_conn.hdel(group_id_name, *group_keys)
            group_members = list(req.redis_conn.smembers(group_members_id_name))
            
            # Remove this group from all members group list
            for member in group_members:
                user_groups_id = USER_GROUPS + member
                pipeline.srem(user_groups_id, group_id_name)
            
            # Now remove all group members
            pipeline.srem(group_members_id_name, *group_members)
            pipeline.execute()
            logger.debug("Deleted group data in database")
            resp.status = falcon.HTTP_OK        


@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'group_item'

    @falcon.before(deserialize)
    #@falcon.after(group_kafka_item_get_producer)
    def on_get(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        group_id_name = GROUP + id
        group_members_id_name = GROUP_MEMBERS + id
        resp.body = req.redis_conn.hgetall(group_id_name)
        # Should we also get members?                
        # This is a get request, so body in req.params
        if 'members' in req.params['query']:
            resp.body['members'] = list(req.redis_conn.smembers(group_members_id_name))
                
        resp.status = falcon.HTTP_FOUND
        
    @falcon.before(deserialize)
    @falcon.after(group_kafka_item_delete_producer)    
    def on_delete(self, req, resp, id):
        # Delete a member
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Deleting member from group data in database ...")
        group_id_name = GROUP + id
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = falcon.HTTP_UNAUTHORIZED
            return
        else:
            group_members_id_name = GROUP_MEMBERS + group_id            
            pipeline = req.redis_conn.pipeline(True)
            pipeline.srem(group_members_id_name, *req.params['query']['member_id'])
            # Remove this group from this member's group list
            for group_member in req.params['query']['member_id']:
                user_groups_id = USER_GROUPS + group_member
                pipeline.srem(user_groups_id, group_id_name)
            pipeline.execute()
            logger.debug("Deleted member from group data in database")
            resp.status = falcon.HTTP_OK

    #@falcon.before(deserialize_update)
    @falcon.before(deserialize)
    @falcon.after(group_kafka_item_put_producer)
    def on_put(self, req, resp, id):        
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Finding group in database ... %s" %repr(id))
        group_id_name = GROUP + id
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = falcon.HTTP_UNAUTHORIZED
            return
        else:
            pipeline = req.redis_conn.pipeline(True)
            for key in req.params['body']:
                pipeline.hset(group_id_name, key, req.params['body'][key])
            pipeline.execute()
        logger.debug("Updated group data in database")
        resp.status = falcon.HTTP_OK

    @falcon.before(deserialize)
    @falcon.after(group_kafka_item_post_producer)
    def on_post(self, req, resp, id):
        # Add a member to group
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Adding member to group in database ... %s" %repr(id))
        group_id_name = GROUP + id
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = falcon.HTTP_UNAUTHORIZED
            return
        else:
            group_members_id_name = GROUP_MEMBERS + id
            logger.debug("Adding members to the group: ")
            pipeline = req.redis_conn.pipeline(True)
            pipeline.sadd(group_members_id_name, *req.params['body']['member_id'])
            for member in req.params['body']['member_id']:
                user_groups_id = USER_GROUPS + member
                pipeline.srem(user_groups_id, group_id_name)                            
            pipeline.execute()
        logger.debug("Added members to group in database")
        resp.status = falcon.HTTP_OK