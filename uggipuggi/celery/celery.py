from __future__ import absolute_import
import os, sys
from celery import Celery

#sys.path.append('/home/dubba/work/webdev/backends/up_be_falcon')
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(ROOT_DIR)

# instantiate Celery object
celery = Celery(include=[
                         'uggipuggi.tasks.resource_add_task',
                         'uggipuggi.tasks.user_tasks',
                        ])

# import celery config file
celery.config_from_object('conf.celeryconfig')

if __name__ == '__main__':
    # cd to project maindir
    # celery -A uggipuggi.celery.celery worker -l debug -n worker.high -Q high        
    celery.start()
