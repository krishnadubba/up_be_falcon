# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging

from uggipuggi.constants import RECIPE, SAVED_RECIPES
from uggipuggi.controllers.hooks import serialize, supply_redis_conn
from uggipuggi.libs.error import HTTPBadRequest, HTTPUnauthorized
from uggipuggi.messaging.user_kafka_producers import user_saved_kafka_item_get_producer


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'user_saved_item'

    # TODO: handle PUT requests
    @falcon.before(supply_redis_conn)
    @falcon.after(serialize)
    @falcon.after(user_saved_kafka_item_get_producer)
    def on_get(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        required_fields = ('images', 'recipe_name', 'likes_count', 
                           'saves_count', 'comments_count')
        recipe_ids = req.redis_conn.zrange(SAVED_RECIPES+id, 0, -1)
        pipeline = req.redis_conn.pipeline(True)
        for recipe_id in recipe_ids:
            pipeline.hmget(RECIPE+recipe_id, *required_fields)
        all_concise_recipes = pipeline.execute()            
        resp.body = {'items': all_concise_recipes, 'count': len(all_concise_recipes)}
        resp.status = falcon.HTTP_OK
        