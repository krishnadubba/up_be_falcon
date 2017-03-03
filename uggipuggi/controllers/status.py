# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
from uggipuggi.controllers.hooks import serialize
from uggipuggi.models.recipe import Recipe
from uggipuggi.libs.error import HTTPServiceUnavailable

logger = logging.getLogger(__name__)


class Status(object):

    def __init__(self):
        pass

    @falcon.after(serialize)
    def on_get(self, req, res):
        logger.info('status request made')
        try:
            Recipe.objects.limit(1)
            res.body = {'ok': True}
            logger.info('database query is successful')
        except Exception:
            logger.error('unable to query database successfully.')
            raise HTTPServiceUnavailable("Snakebite server is currently experiencing issues",
                                         "Unable to query database successfully")
