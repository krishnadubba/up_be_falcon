# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
import requests
import mongoengine
from copy import deepcopy
from google.cloud import storage as gc_storage
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError, \
                               LookUpError, InvalidQueryError 

from uggipuggi.constants import GCS_RECIPE_BUCKET, PAGE_LIMIT
from uggipuggi.controllers.hooks import deserialize, serialize
from uggipuggi.controllers.schema.recipe import RecipeSchema, RecipeCreateSchema
from uggipuggi.models.recipe import Comment, Recipe 
from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.messaging.recipe_kafka_producers import recipe_kafka_collection_post_producer,\
                                                       recipe_kafka_item_put_producer


# -------- BEFORE_HOOK functions
def deserialize_create(req, res, resource, params):
    deserialize(req, res, resource, params, schema=RecipeSchema())

def deserialize_update(req, res, resource, params):
    deserialize(req, res, resource, params, schema=RecipeSchema())


#def deserialize_update(req, res, id, resource):
    #deserialize(req, res, resource, schema=RecipeSchema())

# -------- END functions

logger = logging.getLogger(__name__)

@falcon.after(serialize)
class Collection(object):
    def __init__(self):
        self.kafka_topic_name = 'recipe_collection'
        self.gcs_client = gc_storage.Client()            
        self.gcs_bucket = self.gcs_client.bucket(GCS_RECIPE_BUCKET)

        if not self.gcs_bucket.exists():
            logger.debug("GCS Bucket %s does not exist, creating one" %GCS_RECIPE_BUCKET)
            self.gcs_bucket.create()

        self.img_server = 'https://uggipuggi-1234.appspot.com' #uggipuggi_config['imgserver'].get('img_server_ip')        
        
    @falcon.before(deserialize)
    def on_get(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        query_params = req.params.get('query')

        try:
            # get pagination limits
            start = int(query_params.pop('start', 0))
            limit = int(query_params.pop('limit', PAGE_LIMIT))
            end = start + limit

        except ValueError as e:
            raise HTTPBadRequest(title='Invalid Value',
                                 description='Invalid arguments in URL query:\n{}'.format(e.message))
        # custom filters
        # temp dict for updating query filters
        updated_params = {}
        # For these fields, we want to do a partial search instead of exact match
        # So for example, 'chicken curry' satisfies 'recipe_name=chicken' 
        for item in ['recipe_name', 'description']:
            if item in query_params:
                item_val = query_params.pop(item)
                updated_params['{}__icontains'.format(item)] = item_val

        query_params.update(updated_params)  # update modified params for filtering
        recipes_qset = Recipe.objects(**query_params)[start:end]
        
        recipes = [obj.to_mongo().to_dict() for obj in recipes_qset]        
        # No need to use json_util.dumps here (?)                                     
        resp.body = {'items': recipes, 'count': len(recipes)}        
        resp.status = falcon.HTTP_FOUND
        
    #@falcon.before(deserialize_create)
    @falcon.before(deserialize)    
    @falcon.after(recipe_kafka_collection_post_producer)
    def on_post(self, req, resp):
        # Add recipe
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        # save to DB
        if 'multipart/form-data' in req.content_type:
            img_data = req.get_param('images')
            recipe_data = {}
            for key in req._params:
                if key in Recipe._fields and key not in ['images']:
                    if isinstance(Recipe._fields[key], mongoengine.fields.ListField):
                        recipe_data[key] = req.get_param_as_list(key)
                    else:    
                        recipe_data[key] = req.get_param(key)                    
                    
            logger.debug(recipe_data)
            recipe = Recipe(**recipe_data)
            recipe.save()
            res = requests.post(self.img_server + '/img_post', 
                                files={'img': img_data.file}, 
                                data={'gcs_bucket': GCS_RECIPE_BUCKET,
                                      'file_name': str(recipe.id) + '_' + 'recipe_images.jpg',
                                      'file_type': img_data.type
                                     })
            logger.debug(res.status_code)
            logger.debug(res.text)
            if repr(res.status_code) == '200':
                img_url = res.text
                logger.debug("Display_pic public url:")
                logger.debug(img_url)        
                recipe.update(images=[img_url])
                resp.body = {"recipe_id": str(recipe.id), "images": [img_url]}
            else:
                resp.body = {"recipe_id": str(recipe.id)}
        else:    
            recipe = Recipe(**req.params['body'])
            recipe.save()
            resp.body = {"recipe_id": str(recipe.id)}
        
        logger.debug("Recipe created with id: %s" %str(recipe.id))
        resp.status = falcon.HTTP_CREATED


@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'recipe_item'

    def _try_get_recipe(self, id):
        try:
            return Recipe.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            logger.error('Invalid recipe ID provided. {}'.format(e))
            raise HTTPBadRequest(title='Invalid Value', description='Invalid recipe ID provided. {}'.format(e))

    @falcon.before(deserialize)
    def on_get(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        recipe = self._try_get_recipe(id)
        # Converting MongoEngine recipe document to dictionary
        resp.body = recipe._data
        resp.status = falcon.HTTP_FOUND
        
    @falcon.before(deserialize)        
    def on_delete(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Deleting recipe data in database ...")
        recipe = self._try_get_recipe(id)
        recipe.delete()
        logger.debug("Deleted recipe data in database")
        resp.status = falcon.HTTP_OK

    #@falcon.before(deserialize_update)
    @falcon.before(deserialize)    
    @falcon.after(recipe_kafka_item_put_producer)
    def on_put(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Finding recipe in database ... %s" %repr(id))
        recipe = self._try_get_recipe(id)
        logger.debug("Updating recipe data in database ...")
        logger.debug(req.params['body'])
        # save to DB
        try:            
            for key, value in req.params['body'].items():
                # Adding comments to the recipe
                if key == 'comment':
                    comment = Comment(content=value['content'], 
                                      user_id=value['user_id'], 
                                      user_name=value['user_name'])
                    recipe.comments.append(comment)
                    recipe.save()
                    resp.recipe_author_id = recipe.user_id
                else:
                    # Updating/adding other fields
                    recipe.update(key=value)                        
        except (ValidationError, LookUpError, InvalidQueryError, KeyError) as e:
            logger.error('Invalid fields provided for recipe. {}'.format(e))
            raise HTTPBadRequest(title='Invalid Value', 
                                 description='Invalid fields provided for recipe. {}'.format(e))            
        logger.debug("Updated recipe data in database")
        resp.body = {"recipe_id": str(recipe.id)}
        resp.status = falcon.HTTP_OK
