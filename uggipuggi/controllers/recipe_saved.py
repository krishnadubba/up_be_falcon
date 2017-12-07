# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging

from uggipuggi.constants import RECIPE, USER_SAVED_RECIPES, RECIPE_SAVED
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.libs.error import HTTPBadRequest, HTTPUnauthorized
from uggipuggi.messaging.recipe_kafka_producers import recipe_saved_kafka_item_post_producer


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'recipe_saved_item'

    # TODO: handle PUT requests
    @falcon.before(deserialize)    
    @falcon.before(supply_redis_conn)
    @falcon.after(serialize)
    @falcon.after(recipe_saved_kafka_item_post_producer)
    def on_post(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        pipeline = req.redis_conn.pipeline(True)
        if req.params['body']['saved']:
            pipeline.sadd(RECIPE_SAVED+id, req.user_id)
            pipeline.zadd(USER_SAVED_RECIPES+req.user_id, RECIPE+id, int(time.time()))
            pipeline.hincrby(RECIPE+id, "saves_count", amount=1)
        else:
            pipeline.srem(RECIPE_SAVED+id, req.user_id)
            pipeline.zrem(USER_SAVED_RECIPES+req.user_id, RECIPE+id)
            pipeline.hincrby(RECIPE+id, "saves_count", amount=-1)
        pipeline.hmget(RECIPE+id, "saves_count")
        resp.body = {"saves_count": pipeline.execute()[-1][0]}
        resp.body['recipe_id'] = id
        logger.debug(resp.body)
        resp.status = falcon.HTTP_OK
        
