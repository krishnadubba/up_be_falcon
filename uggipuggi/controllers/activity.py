# -*- coding: utf-8 -*-

from __future__ import absolute_import
import time
import falcon
import logging
import requests
import mongoengine
from google.cloud import storage as gc_storage
from bson import json_util, ObjectId
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError, \
                               LookUpError, InvalidQueryError

from uggipuggi.constants import GCS_ACTIVITY_BUCKET, PAGE_LIMIT, ACTIVITY, USER_ACTIVITY, USER,\
                                GAE_IMG_SERVER, IMG_STORE_PATH, ACTIVITY_CONCISE_VIEW_FIELDS, RECIPE
from uggipuggi.controllers.image_store import ImageStore
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
#from uggipuggi.controllers.schema.activity import CookingActivitySchema, CookingActivityCreateSchema
from uggipuggi.models.cooking_activity import CookingActivity
from uggipuggi.helpers.logs_metrics import init_logger, init_statsd, init_tracer
from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.messaging.activity_kafka_producers import activity_kafka_collection_post_producer,\
                                                         activity_kafka_item_put_producer


# -------- BEFORE_HOOK functions
#def deserialize_create(req, res, resource, kwargs):
    #deserialize(req, res, resource, schema=CookingActivitySchema())

#def deserialize_update(req, res, id, resource):
    #deserialize(req, res, resource, schema=CookingActivitySchema())

# -------- END functions

logger = init_logger()
statsd = init_statsd('up.controllers.activity')

@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Collection(object):
    def __init__(self):
        self.img_store  = ImageStore(IMG_STORE_PATH)
        self.kafka_topic_name = 'activity_collection'
        self.gcs_client = gc_storage.Client()            
        self.gcs_bucket = self.gcs_client.bucket(GCS_ACTIVITY_BUCKET)

        if not self.gcs_bucket.exists():
            logger.debug("GCS Bucket %s does not exist, creating one" %GCS_ACTIVITY_BUCKET)
            self.gcs_bucket.create()

    @falcon.before(deserialize)
    @statsd.timer('get_activity_collection_get')
    def on_get(self, req, resp):
        statsd.incr('get_activity_collection.invocations')
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
        # Retrieve only a subset of fields using only(*list_of_required_fields)
        activities_qset = CookingActivity.objects(**query_params).only(*ACTIVITY_CONCISE_VIEW_FIELDS)[start:end]
        # Is this faster?
        # [obj._data for obj in activities_qset._iter_results()]
        activities = [obj.to_mongo() for obj in activities_qset]
        logger.debug("Query results: %d" %len(activities))
        if activities_qset.count() > 0:
            logger.debug("Sample result:")
            logger.debug(activities[0].to_dict())
        # No need to use json_util.dumps here (?)                             
        resp.body = {'items': [res.to_dict() for res in activities],
                     'count': activities_qset.count()}
                                    
        resp.status = falcon.HTTP_OK
        
    #@falcon.before(deserialize_create)
    @falcon.before(deserialize)    
    @falcon.after(activity_kafka_collection_post_producer)
    @statsd.timer('post_activity_collection_post')
    def on_post(self, req, resp):
        statsd.incr('post_activity.invocations')
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        
        # save to DB
        activity_data = {}
        user_display_pic, user_display_name = req.redis_conn.hmget(USER+req.user_id, "display_pic", 'display_name')
        activity_data['author_avatar'] = user_display_pic
        activity_data['author_display_name'] = user_display_name
        if 'multipart/form-data' in req.content_type:
            img_data = req.get_param('images')
            for key in req._params:
                if key in CookingActivity._fields and key not in ['images']:
                    if isinstance(CookingActivity._fields[key], mongoengine.fields.ListField):
                        activity_data[key] = req.get_param_as_list(key)
                    else:    
                        activity_data[key] = req.get_param(key)                    
                    
            activity_data['recipe_name'] = req.redis_conn.hmget(RECIPE+activity_data['recipe_id'], "recipe_name")[0]
            logger.debug(activity_data)
            activity = CookingActivity(**activity_data)
            activity.save()
            resp.body   = {"activity_id": str(activity.id)}
            
            img_url = ''
            image_name = '_'.join([str(activity.id), str(int(time.time())), 'activity_images'])
            try:
                img_url = self.img_store.save(img_data.file, image_name, img_data.type)                
            except IOError:
                raise HTTPBadRequest(title='Activity_pic storing failed', 
                                     description='Activity_pic upload to cloud storage failed!') 
            activity.update(images=[img_url])
            resp.body.update({"images": [img_url]})                
        else:
            activity_data['recipe_name'] = req.redis_conn.hmget(RECIPE+req.params['body']['recipe_id'], "recipe_name")[0]
            activity = CookingActivity(**activity_data.update(req.params['body']))
            activity.save()
            resp.body = {"activity_id": str(activity.id)}
                    
        activity.update(generation_time=activity.id.generation_time.strftime("%Y-%m-%d %H:%M"))                    
        # Create activity concise view in Redis
        activity_dict = dict(activity._data)
        activity_dict['generation_time'] = activity.id.generation_time.strftime("%Y-%m-%d %H:%M")
        concise_view_dict = {key:activity_dict[key] for key in ACTIVITY_CONCISE_VIEW_FIELDS}
        # redis does not accept lists, so convert it to string
        concise_view_dict['images'] = str(activity_dict['images'])
        concise_view_dict['id'] = str(concise_view_dict['id'])
        req.redis_conn.hmset(ACTIVITY+str(activity.id), concise_view_dict)
        
        req.redis_conn.zadd(USER_ACTIVITY+req.user_id, {str(activity.id): int(time.time())})
        logger.debug("Cooking Activity created with id: %s" %str(activity.id))
        resp.status = falcon.HTTP_OK


@falcon.before(supply_redis_conn)
@falcon.after(serialize)
class Item(object):
    def __init__(self):
        self.kafka_topic_name = 'activity_item'
        
    def _try_get_activity(self, id):
        try:
            return CookingActivity.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            logger.error('Invalid cooking actibity ID provided. {}'.format(e))
            raise HTTPBadRequest(title='Invalid Value', description='Invalid CookingActivity ID provided. {}'.format(e))
    
    @falcon.before(deserialize)
    @statsd.timer('get_activity_get')
    def on_get(self, req, resp, id):
        statsd.incr('get_activity.invocations')
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        activity    = self._try_get_activity(id)
        resp.body   = activity._data
        resp.status = falcon.HTTP_OK

    @falcon.before(deserialize)
    @statsd.timer('delete_activity_delete')
    def on_delete(self, req, resp, id):
        statsd.incr('delete_activity.invocations')
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Deleting activity item in database ...")
        activity = self._try_get_activity(id)
        activity.delete()
        # Remove activity from users activity list in Redis database
        req.redis_conn.zrem(USER_ACTIVITY+req.user_id, id)
        logger.debug("Deleted activity item in database")
        resp.status = falcon.HTTP_OK

    # TODO: handle PUT requests
    #@falcon.before(deserialize_update)
    @falcon.before(deserialize)
    @falcon.after(activity_kafka_item_put_producer)
    @statsd.timer('update_activity_put')
    def on_put(self, req, resp, id):
        statsd.incr('update_activity.invocations')
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        logger.debug("Finding activity in database ... %s" %repr(id))
        activity = self._try_get_activity(id)
        logger.debug("Updating activity item in database ...")
        logger.debug(req.params['body'])
        
        if 'multipart/form-data' in req.content_type:
            img_data = req.get_param('images')
            activity_data = {}
            for key in req._params:
                if key in CookingActivity._fields and key not in ['images']:
                    if isinstance(CookingActivity._fields[key], mongoengine.fields.ListField):
                        activity_data[key] = req.get_param_as_list(key)
                    else:    
                        activity_data[key] = req.get_param(key)
                        
            res = requests.post(GAE_IMG_SERVER + '/img_post', 
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
        else:
            activity_data = req.params['body']

        # save to DB
        try:
            for key, value in activity_data.items():
                if key == 'comment':
                    comment = Comment(content=value['content'], user_id=value['user_id'])
                    activity.comments.append(comment)
                    activity.save()
                    resp.activity_author_id = activity.user_id
                else:                    
                    activity.update(key=value)
                    
            # Updating activity concise view in Redis
            concise_view_dict = {key:activity_data[key] for key in ACTIVITY_CONCISE_VIEW_FIELDS if key in activity_data}
            # redis does not accept lists or python objects, so converting to strings
            if 'images' in concise_view_dict:
                concise_view_dict['images'] = str(activity_data['images'])
            concise_view_dict['id'] = str(concise_view_dict['id'])
            if len(concise_view_dict) > 0:
                req.redis_conn.hmset(ACTIVITY+id, concise_view_dict)
                
        except (ValidationError, LookUpError, InvalidQueryError, KeyError) as e:
            logger.error('Invalid fields provided for cooking activity. {}'.format(e))
            raise HTTPBadRequest(title='Invalid Value', 
                                 description='Invalid fields provided for cooking activity. {}'.format(e))
        logger.debug("Updated activity item in database")
        resp.body = {"activity_id": str(activity.id)}
        resp.status = falcon.HTTP_OK
