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
from dummy_data import feeds, materials, users, recipes, groups, contacts, following

food_gcs_base = 'https://storage.googleapis.com/up_food_pics/'
users_gcs_base = 'https://storage.googleapis.com/up_users_avatars/'
#rest_api = 'http://0.0.0.0:8000/'
rest_api = 'http://35.197.239.67:80/'

# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.DEBUG,
                    #format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    format='%(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/uggipuggi.log',
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

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


count = 0
users_map = {}
recipe_map = {}
activity_map = {}
header = {'Content-Type':'application/json'}

for user in users:
    current_author_id = user['id']
    logging.debug("User: %s" %user)
    payload = {"email": get_dummy_email(count),
               "password": get_dummy_password(count),
               "phone": get_dummy_phone(count),
               "country_code": "IN",
               "display_name": user['name'],
               "gender": user['sex'],
               'display_pic': users_gcs_base + user['avatar'].split('/')[-1]
              }
    
    users_map[current_author_id] = payload
    r = requests.post(rest_api + 'register', data=json.dumps(payload), 
                      headers=header)
    logging.info('Registering User:')    
    curl_request(rest_api + 'register', 'post', header, payload)
    logging.info('Response:')
    logging.info(r)
    logging.info(r.content)
    
    verify_token = json.loads(r.content.decode('utf-8'))['auth_token']
    
    header.update({'auth_token':verify_token})
    r = requests.post(rest_api + 'verify', data=json.dumps({'code':'9999'}), 
                          headers=header)
    
    logging.info('Verifying User:')    
    curl_request(rest_api + 'verify', 'post', header, {'code':'9999'})
    logging.info('Response:')
    logging.info(r)
    logging.info(r.content)    

    header = {'Content-Type':'application/json'}
    r = requests.post(rest_api + 'login', data=json.dumps({'email':users_map[current_author_id]["email"], 
                                                           "password":users_map[current_author_id]["password"]}), 
                      headers=header)
    
    logging.info('Login User:')    
    curl_request(rest_api + 'login', 'post', header, {'email':users_map[current_author_id]["email"], 
                                                      "password":users_map[current_author_id]["password"]})
    logging.info('Response:')
    logging.info(r)
    logging.info(r.content)        

    login_token   = json.loads(r.content.decode('utf-8'))['auth_token']
    user_mongo_id = json.loads(r.content.decode('utf-8'))['user_identifier']
    users_map[current_author_id].update({'login_token':login_token})
    users_map[current_author_id].update({'user_id':user_mongo_id})
    
    count += 1
    #logging.debug(r)
    
logging.info('======= Adding groups ===========')

for group in groups:
    header = {'Content-Type':'application/json'}    
    group_payload = {}
    group_payload['group_name'] = group['group_name']
    group_payload['group_pic'] = group['group_pic']
    login_token = users_map[group['admin']]['login_token']
    header.update({'auth_token':login_token})
    
    r = requests.post(rest_api + 'groups', data=json.dumps(group_payload), 
                      headers=header)

    logging.info('Creating Group:')    
    curl_request(rest_api + 'groups', 'post', header, group_payload)
    logging.info('Response:')
    logging.info(r)
    logging.info(r.content)        
    
    group_id = json.loads(r.content.decode('utf-8'))['group_id']
    logging.debug("group_id: %s" %group_id)
    
    # First memeber is the admin
    member_payload = {}
    member_payload['member_id'] = []
    for member in group['members'][1:]:    
        member_payload['member_id'].append(users_map[member]['user_id'])
        
    r = requests.post(rest_api + 'groups/%s'%group_id, data=json.dumps(member_payload), 
                      headers=header)
    
    logging.info('Adding member(s) to a group:')    
    curl_request(rest_api + 'groups/%s'%group_id, 'post', header, member_payload)
    logging.info('Response:')
    logging.info(r)
    logging.info(r.content)        
    
    r = requests.get(rest_api + 'groups/%s?members=True'%group_id, headers=header)    
    
    logging.info('Getting all members of a group:') 
    curl_request(rest_api + 'groups/%s?members=True'%group_id, 'get', header)
    logging.info('Response:')
    logging.info(r)
    logging.info(r.content)            

    
logging.info('======= Adding contacts ===========')

for contact in contacts:
    header = {'Content-Type':'application/json'}        
    login_token = users_map[contact[0]]['login_token']
    header.update({'auth_token':login_token})
    contact_payload = {}
    contact_payload['contact_user_id'] = []
    for cont in contact[1:]:        
        contact_payload['contact_user_id'].append(users_map[cont]['user_id'])
    r = requests.post(rest_api + 'contacts/%s'%users_map[contact[0]]['user_id'], 
                      data=json.dumps(contact_payload), 
                      headers=header)

    logging.info('Adding contacts of a user:') 
    curl_request(rest_api + 'contacts/%s'%users_map[contact[0]]['user_id'], 'post', header, contact_payload)
    logging.info('Response:')
    logging.info(r)
    logging.info(r.content)

logging.debug('======= Adding Following ===========')

for contact in following:
    header = {'Content-Type':'application/json'}        
    login_token = users_map[contact[0]]['login_token']
    header.update({'auth_token':login_token})
    contact_payload = {}
    for cont in contact[1:]:
        contact_payload = {}
        contact_payload['follower_user_id'] = users_map[cont]['user_id']
        r = requests.post(rest_api + 'following/%s'%users_map[contact[0]]['user_id'], 
                          data=json.dumps(contact_payload), 
                          headers=header)
        
        logging.info('Adding user following another user:') 
        curl_request(rest_api + 'following/%s'%users_map[contact[0]]['user_id'], 'post', header, contact_payload)
        logging.info('Response:')
        logging.info(r)
        logging.info(r.content)        

for user in users:
    current_author_id = user['id']
    # Add all the recipes authored by this user
    for recipe in recipes:
        if recipe['author']['id'] != current_author_id:
            continue
    
        login_token = users_map[current_author_id]['login_token']
        recipe_payload = {"recipe_name": recipe['name'],
                          "user_id": users_map[current_author_id]['user_id'],
                          "likes_count": 0,
                          "user_name": users_map[current_author_id]['display_name'],
                          "images":[food_gcs_base+recipe['image'].split('/')[-1]],
                          "expose_level": 5,
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
        
        logging.info('Adding a recipe by a user:') 
        curl_request(rest_api + 'recipes', 'post', header, recipe_payload)
        logging.info('Response:')
        logging.info(r)
        logging.info(r.content)      
        
        recipe_map[recipe['id']].update({'recipe_id':json.loads(r.content.decode('utf-8'))['recipe_id']})
                                

for recipe in recipes:
    comment = {}
    recipe_id = recipe_map[recipe['id']]['recipe_id']
    for com in recipe['reviews']:                
        comment['comment'] = {}
        user_id = users_map[com['author']['id']]['user_id']
        user_name = users_map[com['author']['id']]['display_name']
        login_token = users_map[com['author']['id']]['login_token']
        header = {'Content-Type':'application/json'}
        header.update({'auth_token':login_token})        
        comment['comment']['user_id'] = user_id
        comment['comment']['user_name'] = user_name
        comment['comment']['content'] = com['content'] 
        r = requests.put(rest_api + 'recipes/%s'%recipe_id, data=json.dumps(comment), 
                         headers=header)
        
        logging.info('Adding comment to a recipe by a user:') 
        curl_request(rest_api + 'recipes/%s'%recipe_id, 'put', header, comment)
        logging.info('Response:')
        logging.info(r)
        logging.info(r.content) 

for feed in feeds:
      
    user_mongo_id = users_map[feed['creator']['id']]['user_id']
    recipe_mongo_id = recipe_map[feed['recipe']['id']]['recipe_id']
    activity_payload = {"recipe_id": recipe_mongo_id,
                        "user_id": user_mongo_id,
                        "user_name": users_map[feed['creator']['id']]['display_name'],
                        "likes_count": 0,
                        "images":recipe_map[feed['recipe']['id']]['images']
                        }
    header = {'Content-Type':'application/json'}
    header.update({'auth_token':users_map[feed['creator']['id']]['login_token']})
    r = requests.post(rest_api + 'activity', data=json.dumps(activity_payload), 
                      headers=header)
    
    logging.info('Adding activity by a user (like cooked a recipe):') 
    curl_request(rest_api + 'activity', 'post', header, activity_payload)
    logging.info('Response:')
    logging.info(r)
    logging.info(r.content)    

    activity_payload.update({'activity_id':json_util.loads(r.content.decode('utf-8'))['activity_id']})
    activity_map[feed['id']] = activity_payload   
    
    activity_Q_payload = {}
    r = requests.get(rest_api + 'activity', params=activity_Q_payload, 
                     headers=header)
    results = json_util.loads(r.content.decode('utf-8'))['items']
    
    #print (json_util.loads(r.content.decode('utf-8'))['count'])
    
#print ("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& User feed &&&&&&&&&&&&&&&&&&&&&&&&&&&&&")

user_mongo_id = users_map['U0016']['user_id']
login_token   =  users_map['U0016']['login_token']
header = {'Content-Type':'application/json'}
header.update({'auth_token':login_token})
             
r = requests.get(rest_api + 'feed/%s'%user_mongo_id, headers=header)

logging.info('Getting user feed to put on his wall:') 
curl_request(rest_api + 'feed/%s'%user_mongo_id, 'get', header)
logging.info('Response:')
logging.info(r)
logging.info(r.content)

#print (r, r.content)    

#print ("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")

all_data = {}
all_data['users'] = users_map
all_data['recipes'] = recipe_map
all_data['activities'] = activity_map
pickle.dump(all_data, open('/tmp/up_dummy_data.p','wb'))

print ("=================")
print ("=================")
