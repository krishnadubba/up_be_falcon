import os, sys, time
import falcon
import requests
from bson import json_util
from celery.utils.log import get_task_logger
from google.cloud import storage as gc_storage

from uggipuggi.celery.celery import celery
from uggipuggi.controllers.hooks import get_redis_conn
from uggipuggi.constants import CONTACTS, FOLLOWERS, USER_FEED, USER_NOTIFICATION_FEED,\
                                RECIPE_COMMENTORS, RECIPE, ACTIVITY, USER, MAX_USER_FEED_LENGTH,\
                                GCS_RECIPE_BUCKET, GAE_IMG_SERVER, IMG_STORE_PATH, FILE_EXT_MAP
from uggipuggi.models.recipe import ExposeLevel

logger = get_task_logger(__name__)


@celery.task
def user_feed_add_recipe(message):
    logger.info('Celery worker: user_feed_add_recipe')
    user_id, expose_level, recipe_id, status, recipe_imgs = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))
    
    redis_conn = get_redis_conn()
    pipeline = redis_conn.pipeline(True)    
    recipe_id_name = RECIPE + recipe_id
    img_urls = []
    for img_file in recipe_imgs:
        img_stream = open(img_file, 'rb')
        res = requests.post(GAE_IMG_SERVER, 
                            files={'img': img_stream}, 
                            data={'gcs_bucket': GCS_RECIPE_BUCKET,
                            'file_name': os.path.basename(img_file), 
                            'file_type': FILE_EXT_MAP[img_file.split('.')[-1]]
                            })
        if repr(res.status_code) == falcon.HTTP_OK.split(' ')[0]:
            img_url = res.text
            logger.debug("Display_pic public url:")
            logger.debug(img_url)
            img_urls.append(img_url)
            
    pipeline.hmset(recipe_id_name, {'images': img_urls})
            
    # Get all contacts and followers userids    
    contacts_id_name  = CONTACTS + user_id
    
    if int(expose_level) == ExposeLevel.FRIENDS:
        recipients = redis_conn.smembers(contacts_id_name)
    elif int(expose_level) == ExposeLevel.PUBLIC:
        followers_id_name = FOLLOWERS + user_id        
        recipients = redis_conn.sunion(contacts_id_name, followers_id_name)
            
    # Add the author to recipe commentor list, so we can notify 
    # him when others comments on this recipe
    recipe_commentors_id = RECIPE_COMMENTORS + recipe_id    
    pipeline.sadd(recipe_commentors_id, user_id)
    
    logger.debug('################# I am executed in celery worker START ###################')
    logger.debug(recipients)
    for recipient in recipients:
        # Use the count of this user feed bucket for notification
        user_feed = USER_FEED + recipient
        pipeline.zadd(user_feed, recipe_id_name, time.time())
        # Remove old feed if the feed is bigger than MAX_USER_FEED_LENGTH posts
        pipeline.zremrangebyrank(user_feed, 0, -MAX_USER_FEED_LENGTH+1)
        #logger.info(redis_conn.zrange(user_feed, 0, -1, withscores=True))
    pipeline.execute()    
    logger.debug('################# I am executed in celery worker END ###################')

@celery.task
def user_feed_put_comment(message):
    logger.debug('Celery worker: user_feed_put_comment')
    commenter_id, commenter_name, recipe_author_id, recipe_id, comment, status = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))        
    redis_conn = get_redis_conn()
    recipe_commentors_id = RECIPE_COMMENTORS + recipe_id
    recipients = redis_conn.smembers(recipe_commentors_id)
    pipeline = redis_conn.pipeline(True)
    # Add the current commentor, so we can notify him when others comments on this recipe
    pipeline.sadd(recipe_commentors_id, commenter_id)
    for recipient in recipients:
        # Use the count of this user feed bucket for notification
        user_notification_feed = USER_NOTIFICATION_FEED + recipient
        pipeline.zadd(user_notification_feed, '__'.join([recipe_id, commenter_id, commenter_name, comment]), 
                      time.time())
        # Send cloud message from here
    pipeline.execute()
    logger.debug('################# I am executed in celery worker ###################')
    
@celery.task
def user_feed_add_activity(message):
    logger.debug('Celery worker: user_feed_add_activity')
    user_id, expose_level, recipe_id, activity_id, status = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))
    
    redis_conn = get_redis_conn()
    pipeline = redis_conn.pipeline(True)
    # Get all contacts and followers userids
    activity_id_name = ACTIVITY + activity_id

    contacts_id_name  = CONTACTS + user_id
    
    if int(expose_level) == ExposeLevel.FRIENDS:
        recipients = redis_conn.smembers(contacts_id_name)
    elif int(expose_level) == ExposeLevel.PUBLIC:
        followers_id_name = FOLLOWERS + user_id        
        recipients = redis_conn.sunion(contacts_id_name, followers_id_name)
        
    for recipient in recipients:
        # Use the count of this user feed bucket for notification
        user_feed = USER_FEED + recipient
        pipeline.zadd(user_feed, activity_id_name, time.time())
        # Remove old feed if the feed is bigger than MAX_USER_FEED_LENGTH posts
        pipeline.zremrangebyrank(user_feed, 0, -MAX_USER_FEED_LENGTH+1)
    pipeline.execute()    
    logger.debug('################# I am executed in celery worker ###################')    