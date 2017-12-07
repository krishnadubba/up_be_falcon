# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging

from uggipuggi.constants import RECIPE, RECIPE_LIKED
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.libs.error import HTTPBadRequest, HTTPUnauthorized
from uggipuggi.messaging.recipe_kafka_producers import recipe_liked_kafka_item_post_producer


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'recipe_liked_item'

    # TODO: handle PUT requests
    @falcon.before(deserialize)
    @falcon.before(supply_redis_conn)
    @falcon.after(serialize)
    @falcon.after(recipe_liked_kafka_item_post_producer)
    def on_post(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        pipeline = req.redis_conn.pipeline(True)
        if req.params['body']['liked']:
            pipeline.sadd(RECIPE_LIKED+id, req.user_id)
            pipeline.hincrby(RECIPE+id, "likes_count", amount=1)
        else:
            pipeline.srem(RECIPE_LIKED+id, req.user_id)
            pipeline.hincrby(RECIPE+id, "likes_count", amount=-1)
        pipeline.hmget(RECIPE+id, "likes_count")
        resp.body = {"likes_count": pipeline.execute()[-1][0]}
        resp.body['recipe_id'] = id
        logger.debug(resp.body)
        resp.status = falcon.HTTP_OK
        
