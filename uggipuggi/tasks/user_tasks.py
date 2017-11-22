import six
import os, sys, time
from bson import json_util
from celery.utils.log import get_task_logger
from uggipuggi.celery.celery import celery
from uggipuggi.models.user import User
from uggipuggi.services.user import get_user 
from uggipuggi.constants import USER, GCS_ALLOWED_EXTENSION, GCS_USER_BUCKET,\
                                BACKEND_ALLOWED_EXTENSIONS
from google.cloud import storage as gc_storage

logger = get_task_logger(__name__)

def check_file_extension(filename, allowed_extensions):
    if ('.' not in filename or
            filename.split('.').pop().lower() not in allowed_extensions):
        raise HTTPBadRequest(title='Invalid image file extention, only .jpg allowed', 
                             description='Invalid image file extention')

@celery.task
def user_profile_pic_task(req_multipart):
    logger.info('Celery worker: user_profile_pic_task')
    logger.info('################# I am executed in celery worker START ###################')
    # We run this under correct google project, we it gets it correct
    # gc_storage.Client(project=current_app.config['PROJECT_ID'])            
    client = gc_storage.Client()
    img_data = req.get_param('display_pic').file.read()
    check_file_extension(req.get_param('display_pic').filename, BACKEND_ALLOWED_EXTENSIONS)
    bucket = client.bucket(GCS_USER_BUCKET)
    blob = bucket.blob(filename)
    blob.upload_from_string(img_data, content_type=req.get_param('display_pic').type)

    url = blob.public_url
    if isinstance(url, six.binary_type):
        url = url.decode('utf-8')
        
    user = get_user('id', req_json.user_id)
    user.update(display_pic=url)
    logger.info('################# I am executed in celery worker END ###################')