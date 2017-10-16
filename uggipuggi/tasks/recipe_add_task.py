import os, sys
from bson import json_util
from uggipuggi.celery.celery import celery

@celery.task
def user_feed_add_recipe(message):
    user_id, activity_id, status = json_util.loads(message.strip("'<>() ").replace('\'', '\"'))
    print('################# I am executed in celery worker ###################')
