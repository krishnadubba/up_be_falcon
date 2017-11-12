# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
from uggipuggi import constants
from uggipuggi.controllers.hooks import deserialize, serialize
from uggipuggi.models.user import User, Role
from uggipuggi.libs.error import HTTPBadRequest, HTTPUnauthorized
from uggipuggi.messaging.user_kafka_producers import user_kafka_item_get_producer
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


# -------- BEFORE_HOOK functions
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

        users_qset = User.objects(**query_params)[start:end]
        users = [obj.to_mongo() for obj in users_qset]
        resp.body = {'items': [res.to_dict() for res in users], 'count': len(users)}
        resp.status = falcon.HTTP_FOUND

class Item(object):
    def __init__(self):
        pass

    def _try_get_user(self, id):
        try:
            return User.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            raise HTTPBadRequest(title='Invalid Value', description='Invalid userID provided. {}'.format(e.message))

    # TODO: handle PUT requests
    @falcon.before(deserialize)
    def on_post(self, req, resp, id):
        user = self._try_get_user(id)
        data = req.params.get('body')
        logger.debug("Updating user data in database ...")
        logger.debug(data)
        # save to DB
        for key, value in data.iteritems():
            user.update(key, value)
            
        logger.debug("Updated user data in database")
        
    @falcon.before(deserialize)        
    def on_delete(self, req, resp, id):
        logger.debug("Checking if user is authorized to request profile delete ...")
        request_user_id = req.user_id        
        request_user = User.objects.get(id=request_user_id)
        if not request_user.role_satisfy(Role.ADMIN):
            # ensure requested user profile delete is request from user him/herself
            if request_user_id != id:
                raise HTTPUnauthorized(title='Unauthorized Request',
                                       description='Not allowed to delete user resource: {}'.format(id))
        logger.debug("Deleting user in database ...")           
        user = self._try_get_user(id)
        user.delete()
        logger.debug("Deleted user in database")
        resp.status = falcon.HTTP_OK
        
    @falcon.before(deserialize)    
    @falcon.after(serialize)
    def on_get(self, req, resp, id):
        request_user_id = req.user_id        
        request_user = User.objects.get(id=request_user_id)
        if not request_user.role_satisfy(Role.EMPLOYEE):
            # ensure requested user profile is request user him/herself
            if request_user_id != id:
                raise HTTPUnauthorized(title='Unauthorized Request',
                                       description='Not allowed to request for user resource: {}'.format(id))
        user = self._try_get_user(id)
        # Converting MongoEngine recipe to dictionary
        resp.body = user._data
        resp.status = falcon.HTTP_FOUND
        
