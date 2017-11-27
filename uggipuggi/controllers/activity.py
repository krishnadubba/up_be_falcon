# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
import requests
import mongoengine
from google.cloud import storage as gc_storage
from bson import json_util, ObjectId
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError, \
                               LookUpError, InvalidQueryError

from uggipuggi.constants import GCS_ACTIVITY_BUCKET, PAGE_LIMIT, ACTIVITY
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
#from uggipuggi.controllers.schema.activity import CookingActivitySchema, CookingActivityCreateSchema
from uggipuggi.models.cooking_activity import CookingActivity
from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.messaging.activity_kafka_producers import activity_kafka_collection_post_producer,\
                                                         activity_kafka_item_put_producer


# -------- BEFORE_HOOK functions
#def deserialize_create(req, res, resource, kwargs):
    #deserialize(req, res, resource, schema=CookingActivitySchema())

#def deserialize_update(req, res, id, resource):
    #deserialize(req, res, resource, schema=CookingActivitySchema())

# -------- END functions

logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Collection(object):
    def __init__(self):
        self.kafka_topic_name = 'activity_collection'
        self.gcs_client = gc_storage.Client()            
        self.gcs_bucket = self.gcs_client.bucket(GCS_ACTIVITY_BUCKET)

        if not self.gcs_bucket.exists():
            logger.debug("GCS Bucket %s does not exist, creating one" %GCS_ACTIVITY_BUCKET)
            self.gcs_bucket.create()

        self.img_server = 'https://uggipuggi-1234.appspot.com' #uggipuggi_config['imgserver'].get('img_server_ip') 
        self.concise_view_fields = ('images', 'recipe_name', 'user_name', 'likes_count', 'description') 
        
    @falcon.before(deserialize)
    def on_get(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        query_params = req.params.get('query')
        logger.debug("Get query params:")
        logger.debug(query_params)
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
        for item in ['user_name', 'recipe_name', 'description']:
            if item in query_params:
                item_val = query_params.pop(item)
                updated_params['{}__icontains'.format(item)] = item_val

        query_params.update(updated_params)  # update modified params for filtering
        
        logger.debug("Get updated query params:")
        logger.debug(query_params)
        logger.debug(start)
        logger.debug(end)
        activities_qset = CookingActivity.objects(**query_params)[start:end]
        # Is this faster?
        # [obj._data for obj in activities_qset._iter_results()]
        activities = [obj.to_mongo() for obj in activities_qset]
        logger.debug("Query results: %d" %len(activities))
        if len(activities) > 0:
            logger.debug("Sample result:")
            logger.debug(activities[0].to_dict())
        # No need to use json_util.dumps here (?)                             
        resp.body = {'items': [res.to_dict() for res in activities],
                     'count': len(activities)}
                                    
        resp.status = falcon.HTTP_FOUND
        
    #@falcon.before(deserialize_create)
    @falcon.before(deserialize)    
    @falcon.after(activity_kafka_collection_post_producer)
    def on_post(self, req, resp):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        
        # save to DB
        if 'multipart/form-data' in req.content_type:
            img_data = req.get_param('images')
            activity_data = {}
            for key in req._params:
                if key in CookingActivity._fields and key not in ['images']:
                    if isinstance(CookingActivity._fields[key], mongoengine.fields.ListField):
                        activity_data[key] = req.get_param_as_list(key)
                    else:    
                        activity_data[key] = req.get_param(key)                    
                    
            logger.debug(activity_data)
            activity = CookingActivity(**activity_data)
            activity.save()
            res = requests.post(self.img_server + '/img_post', 
                                files={'img': img_data.file}, 
                                data={'gcs_bucket': GCS_ACTIVITY_BUCKET,
                                      'file_name': str(activity.id) + '_' + 'activity_images.jpg',
                                      'file_type': img_data.type
                                     })
            logger.debug(res.status_code)
            logger.debug(res.text)
            if repr(res.status_code) == falcon.HTTP_OK.split(' ')[0]:
                img_url = res.text
                logger.debug("Display_pic public url:")
                logger.debug(img_url)        
                activity.update(images=[img_url])
                activity_data.update({'images':[img_url]})
                resp.body = {"activity_id": str(activity.id), "images": [img_url]}
            else:
                resp.body = {"activity_id": str(activity.id)}
        else:            
            activity = CookingActivity(**req.params['body'])
            activity.save()
            resp.body = {"activity_id": str(activity.id)}
            
        # Create activity concise view in Redis
        concise_view_dict = {key:activity_data[key] for key in self.concise_view_fields if key in activity_data}
        if len(concise_view_dict):
            req.redis_conn.hmset(ACTIVITY+str(activity.id), concise_view_dict)
            
        logger.debug("Cooking Activity created with id: %s" %str(activity.id))
        
        resp.status = falcon.HTTP_CREATED


@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'activity_item'
        self.concise_view_fields = ('images', 'recipe_name', 'user_name', 'likes_count', 'description')
        
    def _try_get_activity(self, id):
        try:
            return CookingActivity.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            logger.error('Invalid cooking actibity ID provided. {}'.format(e))
            raise HTTPBadRequest(title='Invalid Value', description='Invalid CookingActivity ID provided. {}'.format(e))
    
    @falcon.before(deserialize)    
    def on_get(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        activity = self._try_get_activity(id)
        resp.body = activity._data
        resp.body = activity._data
        resp.status = falcon.HTTP_FOUND

    @falcon.before(deserialize)
    def on_delete(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Deleting activity data in database ...")
        activity = self._try_get_activity(id)
        activity.delete()
        logger.debug("Deleted activity data in database")
        resp.status = falcon.HTTP_OK

    # TODO: handle PUT requests
    #@falcon.before(deserialize_update)
    @falcon.before(deserialize)
    @falcon.after(activity_kafka_item_put_producer)
    def on_put(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Finding activity in database ... %s" %repr(id))
        activity = self._try_get_activity(id)
        logger.debug("Updating activity data in database ...")
        logger.debug(req.params['body'])
        # save to DB
        try:
            for key, value in req.params['body'].items():
                if key == 'comment':
                    comment = Comment(content=value['content'], user_id=value['user_id'])
                    activity.comments.append(comment)
                    activity.save()
                    resp.activity_author_id = activity.user_id
                else:                    
                    activity.update(key=value)
                    
            # Updating activity concise view in Redis
            concise_view_dict = {key:req.params['body'][key] for key in self.concise_view_fields if key in req.params['body']}
            if len(concise_view_dict) > 0:
                req.redis_conn.hmset(ACTIVITY+id, concise_view_dict)
                
        except (ValidationError, LookUpError, InvalidQueryError, KeyError) as e:
            logger.error('Invalid fields provided for cooking activity. {}'.format(e))
            raise HTTPBadRequest(title='Invalid Value', 
                                 description='Invalid fields provided for cooking activity. {}'.format(e))
        logger.debug("Updated activity data in database")
        resp.body = {"activity_id": str(activity.id)}
        resp.status = falcon.HTTP_OK
