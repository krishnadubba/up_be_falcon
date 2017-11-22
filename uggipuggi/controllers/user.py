# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six
import falcon
import logging
from google.cloud import storage as gc_storage
from PIL import Image
from io import BytesIO, StringIO

from uggipuggi import constants
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.models.user import User, Role
from uggipuggi.libs.error import HTTPBadRequest, HTTPUnauthorized
from uggipuggi.messaging.user_kafka_producers import user_kafka_item_get_producer,\
                                                     user_kafka_item_put_producer
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError
from uggipuggi.tasks.user_tasks import user_profile_pic_task

from uggipuggi.constants import USER, GCS_ALLOWED_EXTENSION, GCS_USER_BUCKET, BACKEND_ALLOWED_EXTENSIONS

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
            size = (64, 64)
            #user_profile_pic_task.delay(req)
            display_pic_filename = req.get_param('display_pic').filename
            self._check_file_extension(display_pic_filename, BACKEND_ALLOWED_EXTENSIONS)
            
            img_data = req.get_param('display_pic').file.read()
            pil_image = Image.open(BytesIO(img_data))
            pil_image.thumbnail(size)
            
            byte_io = BytesIO()
            pil_image.save(byte_io, 'JPEG')
            thumb_img = byte_io.getvalue()
            
            logger.debug("Display_pic filename:")            
            logger.debug(display_pic_filename)            
            
            display_pic_gcs_filename = str(user.id) + '_' + 'display_pic.jpg'
            blob = self.gcs_bucket.blob(display_pic_gcs_filename)
            blob.upload_from_string(img_data, content_type=GCS_ALLOWED_EXTENSION)
            blob.make_public()
        
            thumb_display_pic_gcs_filename = str(user.id) + '_' + 'display_pic_thumb.jpg'
            thumb_blob = self.gcs_bucket.blob(thumb_display_pic_gcs_filename)
            thumb_blob.upload_from_string(thumb_img, content_type=GCS_ALLOWED_EXTENSION)            
            thumb_blob.make_public()
            
            url = blob.public_url
            if isinstance(url, six.binary_type):
                url = url.decode('utf-8')
            
            thumb_url = thumb_blob.public_url
            if isinstance(thumb_url, six.binary_type):
                thumb_url = thumb_url.decode('utf-8')
                
            logger.debug("Display_pic public url:")
            logger.debug(url)
            
            logger.debug("Display_pic thumb public url:")
            logger.debug(thumb_url)
            
            user.update(display_pic=url)
            user.update(dp_thumbnail=thumb_url)
            
            resp.body = url
            data = req._params.copy()
            data.pop("display_pic")
            logger.debug(data)            
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
        
