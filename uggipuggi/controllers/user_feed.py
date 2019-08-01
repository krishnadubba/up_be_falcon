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
            limit = req.params['query'].get('limit', MAX_USER_FEED_LOAD)
            end = start + limit
        except KeyError:
            start = 0
            limit = MAX_USER_FEED_LOAD
            end = start + limit
        # For the time being get all the feed
        user_feed_item_ids = req.redis_conn.zrevrange(user_feed_id, start, end)
        pipeline = req.redis_conn.pipeline(True)
        for feed_id in user_feed_item_ids:
            pipeline.hgetall(feed_id)
        # Only here we supply the key as well because in feed we have both recipes and activities
        # and key starting with "r:" and activity starts with "act:"
        #resp.body = [{k: v} for k, v in zip(user_feed_item_ids, pipeline.execute())]
        resp.body = pipeline.execute()
        #resp.body = [dict(i, images=eval(i['images'])) for i in resp.body]
        # Redis DB stores list as string, so convert back the string to list
        for i in range(len(resp.body)):
            resp.body[i]['images'] = eval(resp.body[i]['images'])
            
        resp.status = falcon.HTTP_OK