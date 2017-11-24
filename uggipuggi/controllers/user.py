# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import six
import sys
import falcon
import logging
import requests

from google.cloud import storage as gc_storage
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError
#sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

#from manage import config as uggipuggi_config
from uggipuggi import constants
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.models.user import User, Role
from uggipuggi.libs.error import HTTPBadRequest, HTTPUnauthorized
from uggipuggi.messaging.user_kafka_producers import user_kafka_item_get_producer,\
                                                     user_kafka_item_put_producer
from uggipuggi.tasks.user_tasks import user_profile_pic_task
from uggipuggi.constants import USER, GCS_ALLOWED_EXTENSION, GCS_USER_BUCKET,\
                                BACKEND_ALLOWED_EXTENSIONS

# -------- BEFORE_HOOK functions
# -------- END functions

logger = logging.getLogger(__name__)

@falcon.before(supply_redis_conn)
class ID(object):
    def __init__(self):
        pass

    @falcon.before(deserialize)
    @falcon.after(serialize)
    def on_post(self, req, resp):
        data = req.params.get('body')
        if 'phone_numbers' not in data:
            raise HTTPBadRequest(title='Invalid Value', description='Please provide phone numbers. {}'.format(e))
        user_ids = req.redis_conn.mget(data['phone_numbers'])
        resp.body = {'items': user_ids, 'count': len(user_ids)}
        resp.status = falcon.HTTP_OK
        
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
                                 description='Invalid arguments in URL query:\n{}'.format(e))

        users_qset = User.objects(**query_params)[start:end]
        users = [obj.to_mongo().to_dict() for obj in users_qset]
        resp.body = {'items': users, 'count': len(users)}
        resp.status = falcon.HTTP_OK

class Item(object):
    def __init__(self):
        self.gcs_client = gc_storage.Client()            
        self.gcs_bucket = self.gcs_client.bucket(GCS_USER_BUCKET)

        if not self.gcs_bucket.exists():
            logger.debug("GCS Bucket %s does not exist, creating one" %GCS_USER_BUCKET)
            self.gcs_bucket.create()

        self.img_server = 'https://uggipuggi-1234.appspot.com' #uggipuggi_config['imgserver'].get('img_server_ip')            
        self.kafka_topic_name = 'user_item'
            
    def _check_file_extension(self, filename, allowed_extensions):
        if ('.' not in filename or
                filename.split('.').pop().lower() not in allowed_extensions):
            raise HTTPBadRequest(title='Invalid image file extention, only .jpg allowed', 
                                 description='Invalid image file extention')    

    def _try_get_user(self, id):
        try:
            return User.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            raise HTTPBadRequest(title='Invalid Value', description='Invalid userID provided. {}'.format(e))

    # TODO: handle PUT requests
    @falcon.before(deserialize)
    @falcon.after(user_kafka_item_put_producer)
    def on_put(self, req, resp, id):
        req.kafka_topic_name = '_'.join([self.kafka_topic_name, req.method.lower()])
        
        user = self._try_get_user(id)
        
        logger.debug("Updating user data in database ...")
        logger.debug(req.content_type)
        # save to DB
        if 'multipart/form-data' in req.content_type:
            # img_data has three components
            # file (the image data that you can see using read()), filename, type
            img_data = req.get_param('display_pic')            

            res = requests.post(self.img_server + '/img_post', 
                                files={'img': img_data.file}, 
                                data={'gcs_bucket': GCS_USER_BUCKET,
                                      'file_name': str(user.id) + '_' + 'display_pic.jpg',
                                      'file_type': img_data.type
                                      })            
            logger.debug(res.status_code)
            logger.debug(res.text)
            if repr(res.status_code) == falcon.HTTP_OK.split(' ')[0]:
                img_url = res.text
                logger.debug("Display_pic public url:")
                logger.debug(img_url)
                
                user.update(display_pic=img_url)
                
                resp.body = img_url
                data = req.get_param('body')
                logger.debug(data)
            else:
                raise HTTPBadRequest(title='Image upload to cloud server failed!',
                                     description='Status Code: %s'%repr(res.status_code))
                
        else:
            data = req.params.get('body')
            logger.debug(data)
            
        # Using dictionary to update fields
        user.update(**data)

        logger.debug("Updated user data in database")
        
        resp.status = falcon.HTTP_OK
        
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
        resp.status = falcon.HTTP_OK
        
