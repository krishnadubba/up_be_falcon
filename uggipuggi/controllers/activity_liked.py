# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging

from uggipuggi.constants import ACTIVITY, ACTIVITY_LIKED
from uggipuggi.controllers.hooks import serialize, supply_redis_conn
from uggipuggi.libs.error import HTTPBadRequest, HTTPUnauthorized
from uggipuggi.messaging.activity_kafka_producers import activity_liked_kafka_item_post_producer


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'activity_liked_item'

    # TODO: handle PUT requests
    @falcon.before(supply_redis_conn)
    @falcon.after(serialize)
    @falcon.after(activity_liked_kafka_item_post_producer)
    def on_post(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        pipeline = req.redis_conn.pipeline(True)
        if req.params['body']['liked']:
            pipeline.sadd(ACTIVITY_LIKED+id, req.user_id)
            pipeline.hincrby(ACTIVITY+id, "likes_count", amount=1)
        else:
            pipeline.srem(ACTIVITY_LIKED+id, req.user_id)
            pipeline.hincrby(ACTIVITY+id, "likes_count", amount=-1)
        pipeline.hmget(ACTIVITY+id, "likes_count")        
        resp.body["likes_count"] = pipeline.execute()[-1]            
        resp.status = falcon.HTTP_OK
        
