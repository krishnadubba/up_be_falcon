# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
from bson import json_util, ObjectId
from uggipuggi import constants
from uggipuggi.controllers.hooks import deserialize, serialize, read_req_body
from uggipuggi.models.user import User, Group
from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.messaging.group_kafka_producers import group_kafka_item_put_producer,\
             group_kafka_item_delete_producer, group_kafka_collection_post_producer
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


# -------- BEFORE_HOOK functions
def deserialize_create(req, res, resource, kwargs):
    deserialize(req, res, resource, schema=RecipeSchema())

def deserialize_update(req, res, id, resource):
    deserialize(req, res, resource, schema=RecipeSchema())

# -------- END functions

logger = logging.getLogger(__name__)

@falcon.after(serialize)
class Collection(object):
    def __init__(self):
        self.kafka_topic_name = 'group_collection'

    @falcon.before(deserialize)    
    def on_get(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
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
        groups_qset = Group.objects(**query_params)[start:end]
        groups = [obj.to_mongo() for obj in groups_qset]
        
        # No need to use json_util.dumps here (?)                             
        resp.body = {'items': [res.to_dict() for res in groups],
                     'count': len(groups)}
        resp.status = falcon.HTTP_FOUND
        
    #@falcon.before(deserialize_create)
    @falcon.before(deserialize)
    @falcon.after(group_kafka_collection_post_producer)
    def on_post(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        # save to DB
        group = Group(**req.params['body'])
        group.save()
        logger.debug("Group created with id: %s" %str(group.id))
        
        # return Recipe id
        resp.body = {"group_id": str(group.id)}
        resp.status = falcon.HTTP_CREATED
        
    @falcon.before(deserialize)
    @falcon.after(group_kafka_collection_delete_producer)
    def on_delete(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        logger.debug("Deleting group data in database ...")
        group = self._try_get_group(req.params['body']['group_id'])
        group.delete()
        logger.debug("Deleted group data in database")
        resp.status = falcon.HTTP_OK        


@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'group_item'

    def _try_get_group(self, id):
        try:
            return Group.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            logger.error('Invalid group ID provided. {}'.format(e.message))
            raise HTTPBadRequest(title='Invalid Value', description='Invalid group ID provided. {}'.format(e.message))

    @falcon.after(deserialize)
    def on_get(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        group = self._try_get_group(id)
        resp.body = recipe.to_group()
        resp.status = falcon.HTTP_FOUND
        
    @falcon.before(deserialize)    
    @falcon.after(group_kafka_item_delete_producer)    
    def on_delete(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        logger.debug("Deleting member from group data in database ...")
        group = self._try_get_group(id)
        group.members.pop(req.params['body']['member_id'])
        logger.debug("Deleted member from group data in database")
        resp.status = falcon.HTTP_OK

    # TODO: handle PUT requests
    #@falcon.before(deserialize_update)
    @falcon.before(deserialize)
    @falcon.after(recipe_kafka_item_put_producer)
    def on_put(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name + req.method.lower()])
        logger.debug("Finding recipe in database ... %s" %repr(id))
        recipe = self._try_get_recipe(id)
        #data = req.params.get('body')
        logger.debug("Updating recipe data in database ...")
        logger.debug(req.params['body'])
        # save to DB
        try:            
            for key, value in req.params['body'].items():
                if key == 'comment':
                    comment = Comment(content=value['content'], user_id=value['user_id'])
                    recipe.comments.append(comment)
                    recipe.save()
                    resp.recipe_author_id = recipe.user_id
                else:    
                    recipe.update(key, value)                        
        except (ValidationError, KeyError) as e:
            logger.error('Invalid fields provided for recipe. {}'.format(e.message))
            raise HTTPBadRequest(title='Invalid Value', 
                                 description='Invalid fields provided for recipe. {}'.format(e.message))            
        logger.debug("Updated recipe data in database")
        resp.body = recipe.id
        resp.status = falcon.HTTP_OK
