# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
from bson import json_util, ObjectId
from uggipuggi import constants
from uggipuggi.controllers.hooks import deserialize, serialize
#from uggipuggi.controllers.schema.activity import CookingActivitySchema, CookingActivityCreateSchema
from uggipuggi.models.cooking_activity import CookingActivity
from uggipuggi.libs.error import HTTPBadRequest
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


# -------- BEFORE_HOOK functions
#def deserialize_create(req, res, resource, kwargs):
    #deserialize(req, res, resource, schema=CookingActivitySchema())

#def deserialize_update(req, res, id, resource):
    #deserialize(req, res, resource, schema=CookingActivitySchema())

# -------- END functions

logger = logging.getLogger(__name__)


class Collection(object):
    def __init__(self):
        pass

    @falcon.before(deserialize)
    @falcon.after(serialize)
    def on_get(self, req, resp):
        query_params = req.params.get('query')

        try:
            # get pagination limits
            start = int(query_params.pop('start', 0))
            limit = int(query_params.pop('limit', constants.PAGE_LIMIT))
            end = start + limit

        except ValueError as e:
            raise HTTPBadRequest(title='Invalid Value',
                                 description='Invalid arguments in URL query:\n{}'.format(e.message))
        # custom filters
        # temp dict for updating query filters
        updated_params = {}

        for item in ['name', 'description']:
            if item in query_params:
                item_val = query_params.pop(item)
                updated_params['{}__icontains'.format(item)] = item_val

        query_params.update(updated_params)  # update modified params for filtering

        activities = CookingActivity.objects(**query_params)[start:end]

        resp.body = json_util.dumps({'items': activities, 'count': len(activities)})
        resp.status = falcon.HTTP_FOUND
        
    #@falcon.before(deserialize_create)
    @falcon.after(serialize)
    def on_post(self, req, resp):
        try:
            req_stream = req.stream.read()
            if isinstance(req_stream, bytes):
                json_body = json_util.loads(req_stream.decode('utf8'))
            else:
                json_body = json_util.loads(req_stream)
            req.params['body'] = json_body    
        except Exception:
            raise falcon.HTTPBadRequest(
                "I don't understand", traceback.format_exc())        

        data = req.params.get('body')  # recipe data
        
        # save to DB
        activity = CookingActivity(**data)
        activity.save()
        logger.debug("Cooking Activity created with id: %s" %str(activity.id))
        
        # return Recipe id
        resp.body = {"activity_id": str(activity.id)}

class Item(object):
    def __init__(self):
        pass

    def _try_get_activity(self, id):
        try:
            return CookingActivity.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:            
            raise HTTPBadRequest(title='Invalid Value', description='Invalid CookingActivity ID provided. {}'.format(e.message))

    @falcon.after(serialize)
    def on_get(self, req, resp, id):
        activity = self._try_get_activity(id)

    @falcon.after(serialize)
    def on_delete(self, req, resp, id):
        activity = self._try_get_activity(id)
        activity.delete()

    # TODO: handle PUT requests
    #@falcon.before(deserialize_update)
    @falcon.after(serialize)
    def on_post(self, req, resp, id):
        activity = self._try_get_activity(id)
        data = req.params.get('body')
        logger.debug("=============")
        logger.debug(data)
        # save to DB
        for key, value in data.iteritems():
            setattr(activity, key, value)
        activity.save()

        activity = CookingActivity.objects.get(id=id)
        resp.body = activity
