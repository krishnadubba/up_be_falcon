# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
import colander
import mongoengine as mongo
from bson import json_util
from uggipuggi.helpers.json import map_query
from uggipuggi.libs.error import HTTPBadRequest, HTTPNotAcceptable

import redis
redis_conn = redis.Redis(host='redis', port=6379, db=0, charset="utf-8", decode_responses=True)

def deserialize(req, res, resource, params, schema=None):
    """
    A BEFORE hook function
    Deserializes data from the request object based on HTTP method
    if a colander Schema is provided, further deserialize data with the schema
    updates req.params with the deserialized data, in either 'body' or 'query' key
    :param req: request object
    :param res: response object
    :param resource: response pbject
    :param params: parameters dict supplied by falcon
    :param schema: colander Schema object
    """

    def _is_json_type(content_type):
        return content_type == 'application/json'

    if req.method.upper() in ['POST', 'PUT', 'PATCH']:

        #if not _is_json_type(req.content_type):
            #raise HTTPNotAcceptable(description='JSON required. '
                                                #'Invalid Content-Type\n{}'.format(req.content_type))

        if _is_json_type(req.content_type):
            req.params['body'] = {}    
            try:
                req_stream = req.stream.read()
                if isinstance(req_stream, bytes):
                    json_body = json_util.loads(req_stream.decode('utf8'))
                else:
                    json_body = json_util.loads(req_stream)
                    
                req.params['body'] = json_body    
            except Exception:
                raise falcon.HTTPBadRequest(
                    "I don't understand the HTTP request body", traceback.format_exc())
        
        else:
            logging.debug(req.content_type)
            
        if schema:
            try:
                json_body = schema.deserialize(json_body)
            except colander.Invalid as e:
                raise HTTPBadRequest(title='Invalid Value',
                                     description='Invalid arguments '
                                                 'in params:\n{}'.format(e.asdict()))

        
    elif req.method.upper() in ['OPTIONS', 'HEAD', 'GET', 'DELETE']:

        req.params['query'] = {}

        if not req.query_string:
            return

        logging.debug("%%%%%%%%%%%%%%%%%%")
        logging.debug("Query String")
        logging.debug(req.query_string)
        logging.debug("%%%%%%%%%%%%%%%%%%")
        
        query = map_query(req.query_string, ignores=['token'])

        if schema:
            try:
                query = schema.deserialize(query)
            except colander.Invalid as e:
                raise HTTPBadRequest(title='Invalid Value',
                                     description='Invalid arguments '
                                                 'in params:\n{}'.format(e.asdict()))

        req.params['query'] = query
        logging.debug("%%%%%%%%%%%%%%%%%%")
        logging.debug(req.params['query'])
        logging.debug("%%%%%%%%%%%%%%%%%%")

def serialize(req, res, resource):
    """
    An AFTER hook function
    Serializes the data from dict to json-formatted string
    :param req: request object
    :param res: response object
    :param resource: resource object
    """
    def _to_json(obj):
        # base cases:
        if isinstance(obj, mongo.Document):
            return obj._data
        if isinstance(obj, dict):
            return {k: _to_json(v) for k, v in obj.items()}
        if isinstance(obj, mongo.queryset.queryset.QuerySet) or isinstance(obj, list):
            return [_to_json(item) for item in obj]
        return obj

    res.body = json_util.dumps(_to_json(res.body))
    
def supply_redis_conn(req, resp, resource, params):
    req.redis_conn = redis_conn
    
def get_redis_conn():
    return redis_conn