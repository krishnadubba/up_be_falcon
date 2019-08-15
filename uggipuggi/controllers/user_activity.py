# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging

from uggipuggi.constants import ACTIVITY, USER_ACTIVITY, ACTIVITY_CONCISE_VIEW_FIELDS
from uggipuggi.controllers.hooks import serialize, supply_redis_conn
from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.helpers.logs_metrics import init_logger, init_statsd, init_tracer
from uggipuggi.messaging.user_kafka_producers import user_activity_kafka_item_get_producer


logger = init_logger()
statsd = init_statsd('up.controllers.user_activity')

@falcon.before(supply_redis_conn)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'user_activity_item'

    # TODO: handle PUT requests
    @falcon.before(supply_redis_conn)
    @falcon.after(serialize)
    @falcon.after(user_activity_kafka_item_get_producer)
    @statsd.timer('get_user_activities_get')
    def on_get(self, req, resp, id):
        statsd.incr('get_user_activity.invocations')
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        activity_ids = req.redis_conn.zrange(USER_ACTIVITY+id, 0, -1)
        pipeline = req.redis_conn.pipeline(True)
        for activity_id in activity_ids:
            pipeline.hmget(ACTIVITY + activity_id, *ACTIVITY_CONCISE_VIEW_FIELDS)
        resp.body = {'items': pipeline.execute(),
                     'fields': ACTIVITY_CONCISE_VIEW_FIELDS, 
                    }
        resp.status = falcon.HTTP_OK
        
