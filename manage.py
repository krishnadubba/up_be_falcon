# -*- coding: utf-8 -*-
from __future__ import absolute_import
from uggipuggi import create_uggipuggi
from conf import get_config
import os

# load config via env
env = os.environ.get('UGGIPUGGI_BACKEND_ENV', 'live')
config = get_config(env)
uggipuggi = create_uggipuggi(**config)

