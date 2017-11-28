# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging

from uggipuggi.constants import ACTIVITY, USER_ACTIVITY
from uggipuggi.controllers.hooks import serialize, supply_redis_conn
from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.messaging.user_kafka_producers import user_activity_kafka_item_get_producer


logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'user_activity_item'

    # TODO: handle PUT requests
    @falcon.before(supply_redis_conn)
    @falcon.after(serialize)
    @falcon.after(user_activity_kafka_item_get_producer)
    def on_get(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        activity_ids = req.redis_conn.zrange(USER_ACTIVITY+id, 0, -1)
        pipeline = req.redis_conn.pipeline(True)
        for activity_id in activity_ids:
            pipeline.hgetall(ACTIVITY + activity_id)
        all_concise_activities = pipeline.execute()            
        resp.body = {'items': all_concise_activities, 'count': len(all_concise_activities)}
        resp.status = falcon.HTTP_OK
        
