# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging
from bson import json_util, ObjectId
from uggipuggi import constants
from uggipuggi.controllers.hooks import deserialize, serialize, read_req_body, supply_redis_conn
from uggipuggi.libs.error import HTTPBadRequest, HTTP_UNAUTHORIZED
from uggipuggi.messaging.group_kafka_producers import group_kafka_item_put_producer, group_kafka_item_post_producer,\
                                             group_kafka_item_delete_producer, group_kafka_collection_post_producer


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
class Collection(object):
    def __init__(self):
        self.kafka_topic_name = 'group_collection'

    @falcon.before(deserialize)
    @falcon.after(serialize)
    def on_get(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        resp.status = falcon.HTTP_FOUND
        
    #@falcon.before(deserialize_create)
    @falcon.before(read_req_body)
    @falcon.after(serialize)
    @falcon.after(group_kafka_collection_post_producer)
    def on_post(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        # Get new group ID
        group_id = str(req.redis_conn.incr('group:'))
        group_id_name = 'group:' + group_id
        
        req.redis_conn.hmset(group_id_name, {
            'group_name': req.body['group_name'],
            'group_pic' : req.body['group_pic'],
            'created_time': time.time(),
            'admin'       : req.user_id
        })
        
        resp.body = {"group_id": group_id_name}
        resp.status = falcon.HTTP_CREATED
        
    @falcon.before(read_req_body)
    @falcon.after(serialize)
    @falcon.after(group_kafka_collection_delete_producer)
    def on_delete(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        logger.debug("Deleting group data in database ...")
        group_id_name = 'group:' + req.body['group_id']
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = HTTP_UNAUTHORIZED
            return
        else:            
            group_keys = list(req.redis_conn.hgetall(group_id_name).keys())
            req.redis_conn.hdel(group_id_name, *group_keys)
            
            group_members_id_name = 'group_members:' + group_id
            group_keys = list(req.redis_conn.hgetall(group_members_id_name).keys())
            req.redis_conn.hdel(group_members_id_name, *group_keys)
            logger.debug("Deleted group data in database")
            resp.status = falcon.HTTP_OK        

class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'group_item'

    @falcon.before(read_req_body)
    @falcon.after(serialize)
    def on_get(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        group_id_name = 'group:' + id
        response = {}
        for key in req.body:
            if key == 'group_id':
                continue
            if key != 'members':
                response[key] = req.redis_conn.hget(group_id_name, key)
            else:
                response[key] = list(req.redis_conn.smembers(group_id_name))
                
        resp.body = response
        resp.status = falcon.HTTP_FOUND
        
    @falcon.before(read_req_body)    
    @falcon.after(serialize)
    @falcon.after(group_kafka_item_delete_producer)    
    def on_delete(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        logger.debug("Deleting member from group data in database ...")
        group_id_name = 'group:' + id
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = HTTP_UNAUTHORIZED
            return
        else:
            group_members_id_name = 'group_members:' + group_id
            req.redis_conn.hdel(group_members_id_name, req.body['member_id'])
            logger.debug("Deleted member from group data in database")
            resp.status = falcon.HTTP_OK

    #@falcon.before(deserialize_update)
    @falcon.before(read_req_body)
    @falcon.after(serialize)
    @falcon.after(recipe_kafka_item_put_producer)
    def on_put(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        logger.debug("Finding group in database ... %s" %repr(id))
        group_id_name = 'group:' + id
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = HTTP_UNAUTHORIZED
            return
        else:
            for key in req.body:
                req.redis_conn.hget(group_id_name, key, req.body[key])
            
        logger.debug("Updated recipe data in database")
        resp.status = falcon.HTTP_OK

    @falcon.before(read_req_body)
    @falcon.after(serialize)
    @falcon.after(recipe_kafka_item_post_producer)
    def on_post(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        logger.debug("Adding member to group in database ... %s" %repr(id))
        group_id_name = 'group:' + id
        admin = req.redis_conn.hget(group_id_name, 'admin')
        if admin != req.user_id:
            logger.debug("User is not the admin: %s , %s" %(admin, req.user_id))
            resp.status = HTTP_UNAUTHORIZED
            return
        else:
            group_members_id_name = 'group_members:' + group_id
            # Can I do this?
            #req.redis_conn.sadd(group_members_id_name, *req.body['member_id'])
            for member in req.body['member_id']:
                req.redis_conn.sadd(group_members_id_name, member)
            
        logger.debug("Added members to group in database")
        resp.status = falcon.HTTP_OK