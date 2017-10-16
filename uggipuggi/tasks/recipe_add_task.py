import os, sys, time
from bson import json_util
from celery.utils.log import get_task_logger
from uggipuggi.celery.celery import celery
from uggipuggi.controllers.hooks import get_redis_conn
from uggipuggi.constants import CONTACTS, FOLLOWERS, USER_FEED, RECIPE_COMMENTORS


logger = get_task_logger(__name__)

@celery.task
def user_feed_add_recipe(message):
    logger.debug('Celery worker: user_feed_add_recipe')
    user_id, recipe_id, status = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))    
    redis_conn = get_redis_conn()
    # Get all contacts and followers userids
    contacts_id_name  = CONTACTS + user_id
    followers_id_name = FOLLOWERS + user_id
    recipients = redis_conn.sunion(contacts_id_name, followers_id_name)
    for recipient in recipients:
        # Use the count of this user feed bucket for notification
        user_feed = USER_FEED + recipient
        redis.conn.zadd(user_feed, recipe_id, time.time())
    logger.debug('################# I am executed in celery worker ###################')

@celery.task
def user_feed_put_comment(message):
    logger.debug('Celery worker: user_feed_put_comment')
    user_id, recipe_author_id, recipe_id, comment, status = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))        
    redis_conn = get_redis_conn()
    recipe_commentors_id = RECIPE_COMMENTORS + recipe_author_id
    redis.conn.sadd(recipe_commentors_id, user_id)
    redis.conn.sadd(recipe_commentors_id, recipe_author_id)
    recipients = redis.conn.smembers(recipe_commentors_id)
    recipients.remove(user_id)
    for recipient in recipients:
        # Use the count of this user feed bucket for notification
        user_feed = USER_FEED + recipient
        redis.conn.zadd(user_feed, '_'.join([recipe_id, user_id, comment]), time.time())
        # Send cloud message from here

    logger.debug('################# I am executed in celery worker ###################')
    
@celery.task
def user_feed_add_activity(message):
    logger.debug('Celery worker: user_feed_add_activity')
    user_id, activity_id, status = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))    
    redis_conn = get_redis_conn()
    # Get all contacts and followers userids
    contacts_id_name  = CONTACTS + user_id
    followers_id_name = FOLLOWERS + user_id
    recipients = redis_conn.sunion(contacts_id_name, followers_id_name)
    for recipient in recipients:
        # Use the count of this user feed bucket for notification
        user_feed = USER_FEED + recipient
        redis.conn.zadd(user_feed, activity_id, time.time())
    logger.debug('################# I am executed in celery worker ###################')    