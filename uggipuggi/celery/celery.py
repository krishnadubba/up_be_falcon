from __future__ import absolute_import
from celery import Celery

# instantiate Celery object
celery = Celery(include=[
                         'uggipuggi.tasks.recipe_add_task'
                        ])

# import celery config file
celery.config_from_object('conf.celeryconfig')

if __name__ == '__main__':
    # cd to project maindir
    # celery -A uggipuggi.celery.celery worker -l debug
    celery.start()
