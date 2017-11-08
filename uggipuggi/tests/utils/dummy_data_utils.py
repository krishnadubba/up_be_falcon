import os, sys
import builtins

ROOT_DIR = os.path.dirname(sys.path[0])
sys.path.append(ROOT_DIR)

from conf import get_config
import traceback
import logging
import jwt
import os
import json
import random
import string
import pickle
import requests

from random import randint
from bson import json_util
from datetime import datetime, timedelta
from passlib.hash import bcrypt as crypt
from uggipuggi.tests.utils.dummy_data import feeds, materials, users, recipes, groups, contacts, following

def curl_request(url, method, headers, payloads=None):
    # construct the curl command from request
    command = "curl -v -H {headers} {data} -X {method} {uri}"
    data = "" 
    if payloads:
        payload_list = ['"{0}":"{1}"'.format(k,v) for k,v in payloads.items()]
        data = " -d '{" + ", ".join(payload_list) + "}'"
    header_list = ['"{0}: {1}"'.format(k, v) for k, v in headers.items()]
    header = " -H ".join(header_list)
    logging.info(command.format(method=method, headers=header, data=data, uri=url))
    
def get_dummy_email(count):
    base_email = 'dksreddy'
    return base_email + repr(count) + '@gmail.com'

def get_dummy_password(count):
    base_password = 'abcd1234'
    return base_password + repr(count)

def get_dummy_phone(count):
    base_phone = '00447901103131'
    return base_phone + repr(count)

def get_dummy_display_name(count):
    base_name = "dksreddy"
    return base_name + repr(count)
