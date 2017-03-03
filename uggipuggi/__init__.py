# -*- coding: utf-8 -*-

from __future__ import absolute_import
#import __builtin__
import builtins
import falcon
import logging
import os
import logging.handlers
import time
from mongoengine import connection
from uggipuggi.controllers import recipe, tag, status, rating, user, batch
from uggipuggi.middlewares.auth import JWTAuthMiddleware
from uggipuggi.constants import DATETIME_FORMAT, AUTH_SHARED_SECRET_ENV


def create_uggipuggi(**config):
    uggipuggi = UggiPuggi(config)
    return uggipuggi


class UggiPuggi(object):

    def __init__(self, config):

        self.config = config

        shared_secret = os.getenv(AUTH_SHARED_SECRET_ENV)
        
        self.app = falcon.API(middleware=[CorsMiddleware(config)])
        # If we need authentication
        #self.app = falcon.API(
            #middleware=[JWTAuthMiddleware(shared_secret),CorsMiddleware(config)]
        #)
        self.logger = self._set_logging()
        self.logger.info("")
        self.logger.info("===========")
        self.logger.info(time.strftime("%c"))
        self.logger.info("===========")
        self._setup_db()
        self._load_routes()

    def _load_routes(self):
        self.logger.info('Loading routes ...')
        self.app.add_route('/recipes', recipe.Collection())
        self.app.add_route('/recipes/{id}', recipe.Item())
        
        self.app.add_route('/users', user.Collection())
        self.app.add_route('/users/{id}', user.Item())

        # batch resources
        self.app.add_route('/batch/recipes', batch.RecipeCollection())

    def _setup_db(self, db_section='mongodb'):
        self.logger.info('connecting to database ...')
        # get all config values about DB
        db_config = self.config[db_section]  # map

        self.logger.info(db_config)
        db_name = db_config.get('name')

        attr_map = {'host': 'str', 'port': 'int', 'username': 'str', 'password': 'str'}

        kwargs = {}
        for key, typ in attr_map.items():
            typecast_fn = getattr(builtins, typ)
            # cast the value from db_config accordingly if key-value pair exists
            kwargs[key] = typecast_fn(db_config.get(key)) if db_config.get(key) else None

        connection.disconnect('default')  # disconnect previous default connection if any

        self.db = connection.connect(db_name, **kwargs)

        self.logger.info('connected to Database: {}'.format(self.db))
        
    def _set_logging(self):
        LOG_SETTINGS = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '(%(asctime)s; %(filename)s:%(lineno)d)'
                              '%(levelname)s: %(message)s ',                            
                    'datefmt': "%Y-%m-%d %H:%M:%S",
                }
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler',
                },
                'rotate_file': {
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': 'logs/uggipuggi_backend.log',
                    'encoding': 'utf8',
                    'maxBytes': 100000,
                    'backupCount': 1,
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'rotate_file'],
                    'level': 'DEBUG',
                },
            }
        }
        log_level = getattr(logging, self.config['logging']['level'].upper())
        LOG_SETTINGS['loggers']['']['level'] = log_level        
        if os.environ.get('UGGIPUGGI_BACKEND_ENV', 'dev') == 'live':
            LOG_SETTINGS['loggers']['']['handlers'] = ['rotate_file']           
        logging.config.dictConfig(LOG_SETTINGS)
        return logging.getLogger(__name__) 
        
class CorsMiddleware():
    def __init__(self,config):
        self.config = config
        self.logger = logging.getLogger(__name__) 
    def process_request(self, req, res):
        config = self.config['cors']        
        allowed_origins = config['allowed_origins'].split(',')
        allowed_headers = config['allowed_headers']
        allowed_methods = config['allowed_methods']

        origin = req.get_header('Origin')
        self.logger.debug(origin)
        header = {'Access-Control-Allow-Headers': allowed_headers}
        if origin in allowed_origins:
            header['Access-Control-Allow-Origin'] = origin
        header['Access-Control-Allow-Methods'] = allowed_methods
        header['Allow'] = allowed_methods
        res.set_headers(header)
