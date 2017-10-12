import os, sys
import builtins
from mongoengine import connection

sys.path.append('../')

from uggipuggi.services.user import get_user
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
from dummy_data import feeds, materials, users, recipes

food_gcs_base = 'https://storage.googleapis.com/up_food_pics/'
users_gcs_base = 'https://storage.googleapis.com/up_users_avatars/'
rest_api = 'http://0.0.0.0:8000/'


# load config via env
#db_section='mongodb'
#env = os.environ.get('UGGIPUGGI_BACKEND_ENV', 'dev')
#config = get_config(env, '/home/krishna/work/app_dev/backend/up_be_falcon/conf/dev.ini')
#db_config = config[db_section]  # map

#db_name = db_config.get('name')

#attr_map = {'host': 'str', 'port': 'int', 'username': 'str', 'password': 'str'}

#kwargs = {}
#for key, typ in attr_map.items():
    #typecast_fn = getattr(builtins, typ)
    ## cast the value from db_config accordingly if key-value pair exists
    #kwargs[key] = typecast_fn(db_config.get(key)) if db_config.get(key) else None

#connection.disconnect('default')  # disconnect previous default connection if any

#db = connection.connect(db_name, **kwargs)

header = {'Content-Type':'application/json'}

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

count = 0
users_map = {}
recipe_map = {}
activity_map = {}
for user in users:
    current_author_id = user['id']
    print (user)
    payload = {"email": get_dummy_email(count),
               "password": get_dummy_password(count),
               "phone": get_dummy_phone(count),
               "country_code": "IN",
               "display_name": user['name'],
               "gender": user['sex'],
               'display_pic': users_gcs_base + user['avatar'].split('/')[-1]
              }
    
    users_map[user['id']] = payload
    r = requests.post(rest_api + 'register', data=json.dumps(payload), 
                      headers=header)
    verify_token = json.loads(r.content.decode('utf-8'))['auth_token']
    
    header.update({'auth_token':verify_token})
    r = requests.post(rest_api + 'verify', data=json.dumps({'code':'9999'}), 
                          headers=header)
    
    header = {'Content-Type':'application/json'}
    r = requests.post(rest_api + 'login', data=json.dumps({'email':users_map[user['id']]["email"], 
                                                           "password":users_map[user['id']]["password"]}), headers=header)
    
    login_token   = json.loads(r.content.decode('utf-8'))['auth_token']
    user_mongo_id = json.loads(r.content.decode('utf-8'))['user_id']
    users_map[user['id']].update({'login_token':login_token})
    users_map[user['id']].update({'user_id':user_mongo_id})
    
    # Add all the recipes authored by this user
    for recipe in recipes:
        if recipe['author']['id'] != current_author_id:
            continue
    
        recipe_payload = {"recipe_name": recipe['name'],
                          "user_id": user_mongo_id,
                          "likes_count": 0,
                          "user_name": users_map[user['id']]['display_name'],
                          "images":[food_gcs_base+recipe['image'].split('/')[-1]],                      
                          }
        steps = []
        for direction in recipe['direction'].split('\n'):
            if direction == '':
                continue
            steps.append(direction)
        recipe_payload.update({"steps":steps})
        
        ingredients = []
        ingredients_imgs   = []
        ingredients_quant  = []
        ingredients_metric = []
        for ig in recipe['ingredients']:
            ingredients_metric.append(ig['unit'])
            ingredients_quant.append(ig['quantity'])
            ingredients_imgs.append(food_gcs_base+ig['material']['image'].split('/')[-1])
            ingredients.append(ig['material']['name'])
            
        recipe_payload.update({'ingredients':ingredients})
        recipe_payload.update({'ingredients_imgs':ingredients_imgs})
        recipe_payload.update({'ingredients_quant':ingredients_quant})
        recipe_payload.update({'ingredients_metric':ingredients_metric})            
        
        recipe_map[recipe['id']] = recipe_payload
        
        header.update({'auth_token':login_token})
        r = requests.post(rest_api + 'recipes', data=json.dumps(recipe_payload), 
                          headers=header)    
                
        recipe_map[recipe['id']].update({'recipe_id':json.loads(r.content.decode('utf-8'))['recipe_id']})
                            
    count += 1
    print (r)
    
print ('==================')    

for recipe in recipes:
    comment = {}
    recipe_id = recipe_map[recipe['id']]['recipe_id']
    for com in recipe['reviews']:                
        comment['comment'] = {}
        user_id = users_map[com['author']['id']]['user_id']
        login_token = users_map[com['author']['id']]['login_token']
        header = {'Content-Type':'application/json'}
        header.update({'auth_token':login_token})        
        comment['comment']['user_id'] = user_id
        comment['comment']['content'] = com['content'] 
        r = requests.put(rest_api + 'recipes/%s'%recipe_id, data=json.dumps(comment), 
                         headers=header)        
        print (r)

for feed in feeds:
      
    user_mongo_id = users_map[feed['creator']['id']]['user_id']
    recipe_mongo_id = recipe_map[feed['recipe']['id']]['recipe_id']
    activity_payload = {"recipe_id": recipe_mongo_id,
                        "user_id": user_mongo_id,
                        "likes_count": 0,
                        }
    header = {'Content-Type':'application/json'}
    header.update({'auth_token':users_map[feed['creator']['id']]['login_token']})
    r = requests.post(rest_api + 'activity', data=json.dumps(activity_payload), 
                      headers=header)
    activity_payload.update({'activity_id':json_util.loads(r.content.decode('utf-8'))['activity_id']})
    activity_map[feed['id']] = activity_payload   
    
    #activity_Q_payload = {"user_id": user_mongo_id}
    activity_Q_payload = {}
    r = requests.get(rest_api + 'activity', params=activity_Q_payload, 
                     headers=header)
    results = json_util.loads(r.content.decode('utf-8'))['items']
    
    print (json_util.loads(r.content.decode('utf-8'))['count'])
    
all_data = {}
all_data['users'] = users_map
all_data['recipes'] = recipe_map
all_data['activities'] = activity_map
pickle.dump(all_data, open('/tmp/up_dummy_data.p','wb'))

print ("=================")
print ("=================")