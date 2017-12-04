# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging
from uggipuggi.constants import USER_FEED, MAX_USER_FEED_LOAD
from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.controllers.hooks import serialize, supply_redis_conn


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'user_feed_item'

    #@falcon.after(group_kafka_item_get_producer)
    def on_get(self, req, resp):        
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        user_feed_id = USER_FEED + req.user_id
        try:
            start = req.params['query'].get('start', 0)
            end   = req.params['query'].get('end', 50)
        except KeyError:
            start = 0
            end   = MAX_USER_FEED_LOAD
        # For the time being get all the feed
        user_feed_item_ids = req.redis_conn.zrevrange(user_feed_id, start, end)
        pipeline = req.redis_conn.pipeline(True)
        for feed_id in user_feed_item_ids:
            pipeline.hgetall(feed_id)
        resp.body = {k: v for k, v in zip(user_feed_item_ids, pipeline.execute())}
        resp.status = falcon.HTTP_OK