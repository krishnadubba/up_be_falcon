import os, sys, time
from bson import json_util
from celery.utils.log import get_task_logger
from uggipuggi.celery.celery import celery
from uggipuggi.controllers.hooks import get_redis_conn
from uggipuggi.constants import CONTACTS, FOLLOWERS, USER_FEED, USER_NOTIFICATION_FEED,\
                                RECIPE_COMMENTORS, RECIPE, ACTIVITY, USER, MAX_USER_FEED_LENGTH
from uggipuggi.models.recipe import ExposeLevel

logger = get_task_logger(__name__)

@celery.task
def user_feed_add_recipe(message):
    logger.info('Celery worker: user_feed_add_recipe')
    user_id, user_name, recipe_name, expose_level, recipe_id, recipe_pic, _ = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))
    recipe_dict = {'author_id':user_id, 'author_name':user_name, 'recipe_name':recipe_name,
                   'recipe_pic':recipe_pic, 'type': 'recipe'}
    
    redis_conn = get_redis_conn()
    # Get all contacts and followers userids
    recipe_id_name    = RECIPE + recipe_id
    contacts_id_name  = CONTACTS + user_id
    followers_id_name = FOLLOWERS + user_id
    
    if expose_level == ExposeLevel.FRIENDS:
        recipients = redis_conn.smembers(contacts_id_name)
    elif expose_level == ExposeLevel.PUBLIC:
        recipients = redis_conn.sunion(contacts_id_name, followers_id_name)
        
    pipeline = redis_conn.pipeline(True)
    
    # Add the author to recipe commentor list, so we can notify 
    # him when others comments on this recipe
    recipe_commentors_id = RECIPE_COMMENTORS + recipe_id    
    pipeline.sadd(recipe_commentors_id, user_id)
    
    # Add a hash for the recipe at "recipe:recipe_id"
    pipeline.hmset(recipe_id_name, recipe_dict)
    logger.info('################# I am executed in celery worker START ###################')
    logger.info(recipients)
    for recipient in recipients:
        # Use the count of this user feed bucket for notification
        user_feed = USER_FEED + recipient
        pipeline.zadd(user_feed, recipe_id_name, time.time())
        # Remove old feed if the feed is bigger than MAX_USER_FEED_LENGTH posts
        pipeline.zremrangebyrank(user_feed, 0, -MAX_USER_FEED_LENGTH+1)
        #logger.info(redis_conn.zrange(user_feed, 0, -1, withscores=True))
    pipeline.execute()
    logger.info('################# I am executed in celery worker END ###################')

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
    user_id, recipe_id, activity_pic, activity_id, _ = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))
    
    redis_conn = get_redis_conn()
    pipeline = redis_conn.pipeline(True)
    # Get all contacts and followers userids
    activity_id_name = ACTIVITY + activity_id
    recipe_id_name   = RECIPE   + recipe_id
    
    recipe_name, recipe_author_name, recipe_author_id = redis_conn.hmget(recipe_id_name, ['recipe_name',
                                                                                          'author_name',
                                                                                          'author_id'])    
    activity_dict = {'author_id':user_id, 'author_name':user_name, 'recipe_name':recipe_name,
                     'recipe_pic':activity_pic, 'recipe_author_name':recipe_author_name,
                     'recipe_author_id':recipe_author_id, 'type': 'activity'}
    
    redis_conn.hmset(activity_id_name, activity_dict)
    
    contacts_id_name  = CONTACTS + user_id
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