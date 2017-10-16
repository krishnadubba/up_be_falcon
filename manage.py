# -*- coding: utf-8 -*-
from __future__ import absolute_import
from uggipuggi import UggiPuggi
from conf import get_config
import os

# load config via env
os.environ['CELERY_CONFIG_MODULE'] = 'conf.celeryconfig'
env = os.environ.get('UGGIPUGGI_BACKEND_ENV', 'dev')
config = get_config(env)
uggipuggi = UggiPuggi(config)