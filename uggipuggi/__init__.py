# -*- coding: utf-8 -*-

from __future__ import absolute_import
#import __builtin__
import os
import time
import builtins
import falcon
import logging
import logging.config as logging_config
import logging.handlers
from falcon_cors import CORS

from bson import json_util
from mongoengine import connection as mongo_connection
from falcon_multipart.middleware import MultipartMiddleware
from uggipuggi.controllers import recipe, tag, status, rating, user, user_feed, batch, activity,\
                                  redis_group, redis_contacts, redis_followers, redis_following,\
                                  user_recipes, user_activity, image_store, saved_recipes, Ping,\
                                  group_recipes, recipe_saved, recipe_liked, activity_liked 
from uggipuggi.services.user import get_user  
from uggipuggi.middlewares import auth_jwt
from uggipuggi.middlewares.prometheus_middleware import PrometheusMiddleware
from uggipuggi.helpers.logs_metrics import init_logger, init_statsd, init_tracer
from uggipuggi.constants import DATETIME_FORMAT, AUTH_SHARED_SECRET_ENV, \
                                MAX_TOKEN_AGE, TOKEN_EXPIRATION_SECS,\
                                VERIFY_PHONE_TOKEN_EXPIRATION_SECS, SERVER_RUN_MODE

       
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
        self.forgot_password, self.register, self.logout, self.pw_change, self.verify_phone, self.auth_middleware = auth_jwt.get_auth_objects(
            get_user,
            shared_secret, # random secret
            TOKEN_EXPIRATION_SECS,
            VERIFY_PHONE_TOKEN_EXPIRATION_SECS,
            token_opts=COOKIE_OPTS
        )
        
        cors = CORS(
            allow_all_origins=True,
            allow_all_headers=True,            
            allow_all_methods=True,
            allow_credentials_all_origins=True
        )
        
        self.prometheus_metrics = PrometheusMiddleware()
        self.app = falcon.API(middleware=[cors.middleware,
                                          MultipartMiddleware(),
                                          self.auth_middleware,
                                          self.prometheus_metrics])

        if SERVER_RUN_MODE == 'DEBUG':
            self.logger = self._set_logging()
        else:
            self.logger = init_logger() 
        self.logger.info("")
        self.logger.info("===========")
        self.logger.info(time.strftime("%c"))
        self.logger.info("===========")
        self._setup_db()
        self._load_routes()

    def _load_routes(self):
        self.logger.info('Loading routes ...')
        self.app.add_route('/ping', Ping())
        self.app.add_route('/metrics', self.prometheus_metrics)
        
        self.app.add_route('/recipes', recipe.Collection())
        self.app.add_route('/recipes/{id}', recipe.Item())
        
        self.app.add_route('/activity', activity.Collection())
        self.app.add_route('/activity/{id}', activity.Item())
        
        self.app.add_route('/get_userid', user.ID())
        self.app.add_route('/users', user.Collection())
        self.app.add_route('/users/{id}', user.Item())
        
        self.app.add_route('/recipe_liked/{id}', recipe_liked.Item())
        self.app.add_route('/recipe_saved/{id}', recipe_saved.Item())
        self.app.add_route('/activity_liked/{id}', activity_liked.Item())
        
        self.app.add_route('/saved_recipes/{id}', saved_recipes.Item())
        self.app.add_route('/user_recipes/{id}', user_recipes.Item())
        self.app.add_route('/user_activity/{id}', user_activity.Item())
        
        self.app.add_route('/feed', user_feed.Item())
        
        self.app.add_route('/groups', redis_group.Collection())
        self.app.add_route('/groups/{id}', redis_group.Item())
        self.app.add_route('/group_recipes/{id}', group_recipes.Item())
        
        self.app.add_route('/contacts/{id}', redis_contacts.Item())
        self.app.add_route('/followers/{id}', redis_followers.Item())
        self.app.add_route('/following/{id}', redis_following.Item())
        
        self.app.add_route('/register', self.register)
        self.app.add_route('/verify', self.verify_phone)
        self.app.add_route('/logout', self.logout)
        self.app.add_route('/forgot_password', self.forgot_password)
        self.app.add_route('/password_change', self.pw_change)
        self.app.add_route('/images/{id}', image_store.Item())
        
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

        mongo_connection.disconnect('default')  # disconnect previous default connection if any

        self.db = mongo_connection.connect(db_name, **kwargs)

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
        self.logger = init_logger()
        self.allowed_origins = config['cors']['allowed_origins'].split(',')
        self.allowed_headers = config['cors']['allowed_headers']
        self.allowed_methods = config['cors']['allowed_methods']
        
    def process_request(self, req, res):
        origin = req.get_header('Origin')
        self.logger.debug("Request origin URL:")
        self.logger.debug(origin)
        header = {'Access-Control-Allow-Headers': self.allowed_headers}
        if ('*' in self.allowed_origins and origin != None) or origin in self.allowed_origins:
            self.logger.debug("This origin is allowed")
        if req.method.lower() == 'options':
            res.status = falcon.HTTP_OK
            
        header['Access-Control-Allow-Origin'] = "*"
        header['Access-Control-Allow-Methods'] = self.allowed_methods
        header['Access-Control-Allow-Credentials'] = "true"
        header['Allow'] = self.allowed_methods
        res.set_headers(header)
