import os, sys, time
import falcon
import requests
from bson import json_util
from celery.utils.log import get_task_logger

from uggipuggi.models import ExposeLevel
from uggipuggi.celery.celery import celery
from uggipuggi.services.recipe import get_recipe
from uggipuggi.services.activity import get_activity
from uggipuggi.models.recipe import Comment, Recipe
from uggipuggi.models.cooking_activity import CookingActivity
from uggipuggi.controllers.hooks import get_redis_conn
 
from uggipuggi.services.db_service import get_mongodb_connection
from uggipuggi.controllers.utils.gcloud_utils import upload_image_to_gcs
from uggipuggi.constants import CONTACTS, FOLLOWERS, USER_FEED, USER_NOTIFICATION_FEED,\
                                RECIPE_COMMENTORS, RECIPE, ACTIVITY, USER, MAX_USER_FEED_LENGTH,\
                                GCS_RECIPE_BUCKET, GCS_ACTIVITY_BUCKET, GAE_IMG_SERVER, PUBLIC_RECIPES

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
        (status_code, img_url) = upload_image_to_gcs(img_file, GAE_IMG_SERVER, GCS_RECIPE_BUCKET)
        if img_url:
            img_urls.append(img_url)
        else:
            logger.error('Image upload to cloud server failed with status code: %s' %status_code)
            
    pipeline.hmset(recipe_id_name, {'images': img_urls})
            
    # Get all contacts and followers userids    
    contacts_id_name  = CONTACTS + user_id
    
    if int(expose_level) == ExposeLevel.FRIENDS:
        recipients = redis_conn.smembers(contacts_id_name)
    elif int(expose_level) == ExposeLevel.PUBLIC:
        followers_id_name = FOLLOWERS + user_id        
        recipients = redis_conn.sunion(contacts_id_name, followers_id_name)
        pipeline.zadd(PUBLIC_RECIPES, recipe_id_name, int(time.time()))
            
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
    
    mongo_conn = get_mongodb_connection()
    recipe = get_recipe(recipe_id)
    if recipe:
        recipe.update(**{"images": img_urls})
    else:
        logger.error('Recipe not found: %s' %recipe_id)
        
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
    user_id, expose_level, recipe_id, activity_id, status, activity_imgs = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))
    
    redis_conn = get_redis_conn()
    pipeline = redis_conn.pipeline(True)
    # Get all contacts and followers userids
    activity_id_name = ACTIVITY + activity_id

    img_urls = []
    for img_file in activity_imgs:
        (status_code, img_url) = upload_image_to_gcs(img_file, GAE_IMG_SERVER, GCS_ACTIVITY_BUCKET)
        if img_url:
            img_urls.append(img_url)
        else:
            logger.error('Image upload to cloud server failed with status code: %s' %status_code)
            
    pipeline.hmset(activity_id_name, {'images': img_urls})
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
    
    mongo_conn = get_mongodb_connection()
    activity = get_activity(activity_id)
    if activity:
        activity.update(**{'images': img_urls})
    else:
        logger.error('Recipe not found: %s' %activity_id)
    
    logger.debug('################# I am executed in celery worker ###################')    