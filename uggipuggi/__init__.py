# -*- coding: utf-8 -*-

from __future__ import absolute_import
#import __builtin__
import os
import builtins
import falcon
import logging
import logging.config as logging_config
import logging.handlers
import time
from mongoengine import connection
from uggipuggi.controllers import recipe, tag, status, rating, user, batch, activity
from uggipuggi.services.user import get_user  
from uggipuggi.middlewares import auth_jwt
from uggipuggi.constants import DATETIME_FORMAT, AUTH_SHARED_SECRET_ENV, \
                                MAX_TOKEN_AGE, TOKEN_EXPIRATION_SECS, VERIFY_PHONE_TOKEN_EXPIRATION_SECS


class UggiPuggi(object):

    def __init__(self, config):

        self.config = config

        shared_secret = os.getenv(AUTH_SHARED_SECRET_ENV, 'uggipuggi')
        
        COOKIE_OPTS = {"name": "auth_token",
                       "location": "header",
                       #"max_age": MAX_TOKEN_AGE,
                       "path": "/recipes",
                       "http_only": True}        

        # LoginResource, AuthMiddleware
        self.forgot_password, self.register, self.pw_change, self.login, self.verify_phone, self.auth_middleware = auth_jwt.get_auth_objects(
            get_user,
            shared_secret, # random secret
            TOKEN_EXPIRATION_SECS,
            VERIFY_PHONE_TOKEN_EXPIRATION_SECS,
            token_opts=COOKIE_OPTS
        )
        
        self.app = falcon.API(middleware=[CorsMiddleware(config), 
                                          self.auth_middleware])
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
        
        self.app.add_route('/activity', activity.Collection())
        self.app.add_route('/activity/{id}', activity.Item())
        
        self.app.add_route('/users', user.Collection())
        self.app.add_route('/users/{id}', user.Item())
        self.app.add_route('/login', self.login)
        self.app.add_route('/register', self.register)
        self.app.add_route('/verify', self.verify_phone)
        self.app.add_route('/forgot_password', self.forgot_password)
        self.app.add_route('/password_change', self.pw_change)
        # batch resources
        self.app.add_route('/batch/recipes', batch.RecipeCollection())
        self.logger.info('Loading routes FINISHED')
        
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
        logging_config.dictConfig(LOG_SETTINGS)
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
            self.logger.debug("This origin is allowed")
            header['Access-Control-Allow-Origin'] = origin
        header['Access-Control-Allow-Methods'] = allowed_methods
        header['Allow'] = allowed_methods
        res.set_headers(header)
