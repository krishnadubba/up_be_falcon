import os
from kombu import Exchange, Queue

BROKER_TRANSPORT = "redis"
BROKER_HOST = "redis"  # Maps to redis host.
BROKER_PORT = 6379     # Maps to redis port.
BROKER_VHOST = "0"     # Maps to database number.

CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = "redis"
CELERY_REDIS_PORT = 6379
CELERY_REDIS_DB = 0

CELERY_IGNORE_RESULT = True

CELERY_QUEUES = (
    Queue('high',   Exchange('high'),   routing_key='high'),
    Queue('normal', Exchange('normal'), routing_key='normal'),
    Queue('low',    Exchange('low'),    routing_key='low'),
)
CELERY_DEFAULT_QUEUE       = 'normal'
CELERY_DEFAULT_EXCHANGE    = 'normal'
CELERY_DEFAULT_ROUTING_KEY = 'normal'
CELERY_ROUTES = {
    # -- HIGH PRIORITY QUEUE -- #
    'uggipuggi.tasks.resource_add_task.user_feed_add_recipe':   {'queue': 'high'},    
    'uggipuggi.tasks.resource_add_task.user_feed_add_activity': {'queue': 'high'},
    # -- NORMAL PRIORITY QUEUE -- #
    'uggipuggi.tasks.resource_add_task.user_feed_put_comment':  {'queue': 'high'},
    'uggipuggi.tasks.user_tasks.user_display_pic_task':  {'queue': 'high'},
    # -- LOW PRIORITY QUEUE -- #
    #'myapp.tasks.close_session': {'queue': 'low'},
}
