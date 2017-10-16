import os, sys
from bson import json_util
from celery.utils.log import get_task_logger
from uggipuggi.celery.celery import celery

logger = get_task_logger(__name__)

@celery.task
def user_feed_add_recipe(message):
    user_id, activity_id, status = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))
    logger.debug('################# I am executed in celery worker ###################')
    