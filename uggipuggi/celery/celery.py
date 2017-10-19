from __future__ import absolute_import
import sys
from celery import Celery

sys.path.append('/home/dubba/work/webdev/backends/up_be_falcon')

# instantiate Celery object
celery = Celery(include=[
                         'uggipuggi.tasks.recipe_add_task'
                        ])

# import celery config file
celery.config_from_object('conf.celeryconfig')

if __name__ == '__main__':
    # cd to project maindir
    # celery -A uggipuggi.celery.celery worker -l debug -n worker.high -Q high
    celery.start()
