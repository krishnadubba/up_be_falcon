import re
import os
import sys
import json
import requests
import subprocess
from locust import HttpLocust, TaskSet, task

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(sys.path[0]))))

from uggipuggi.tests.utils.dummy_data import users as dummy_users,\
                groups as dummy_groups, contacts as dummy_contacts,\
                following as dummy_following, recipes as dummy_recipes, feeds as dummy_feeds
from uggipuggi.tests.utils.dummy_data_utils import get_dummy_email, get_dummy_password,\
                                                 get_dummy_phone, get_dummy_display_name 

USER_CREDENTIALS = list(range(10000))
try:
    UGGIPUGGI_IP = os.environ['UGGIPUGGI_BACKEND_IP']
except KeyError:
    ip_config = subprocess.run(["ifconfig", "docker_gwbridge"], stdout=subprocess.PIPE)
    ip_config = ip_config.stdout.decode('utf-8').split('\n')[1]
    UGGIPUGGI_IP = re.findall(r".+ inet addr:([0-9.]+) .+", ip_config)[0] 
REST_API = 'http://%s/'%UGGIPUGGI_IP

class UggiPuggiTaskSet(TaskSet):
    def on_start(self):
        count = USER_CREDENTIALS.pop()
        self.user_name = get_dummy_display_name(count)
        payload = {"email":    get_dummy_email(count),
                   "password": get_dummy_password(count),
                   "phone":    get_dummy_phone(count),
                   "country_code": "IN",
                   "display_name": self.user_name,
                   "gender": 'female',
                   'display_pic': 'https://storage.googleapis.com/up_users_avatars/salam.png'
                   }
        header = {'Content-Type':'application/json'}
        # If you give dict as body use json=dict or data=json.dumps(dict)
        res = self.client.post('/register', data=json.dumps(payload), 
                               headers=header)
        print("==============================")
        print(res.content.decode('utf-8'))
        verify_token = json.loads(res.content.decode('utf-8'))['auth_token']
        
        header.update({'auth_token':verify_token})
        res = self.client.post('/verify', 
                               data=json.dumps({'code':'9999'}), 
                               headers=header)
        
        payload = {'email':get_dummy_email(count), "password":get_dummy_password(count)}
        header = {'Content-Type':'application/json'}
        res = self.client.post('/login', 
                               data=json.dumps(payload), 
                               headers=header)
        res_dict = json.loads(res.content.decode('utf-8'))
        self.login_token = res_dict['auth_token']
        self.user_id     = res_dict['user_identifier']
        
        # First get a recipe and add it. We will use the recipes id in get_recipe 
        # to measure the load of getting recipe 
        first_recipe_payload = self.get_recipe(0)
        header.update({'auth_token':self.login_token})
        res = self.client.post('/recipes', data=json.dumps(first_recipe_payload),
                               headers=header)
        self.recipe_id = json.loads(res.content.decode('utf-8'))['recipe_id']
        
        # We prepare another recipe and use it to measure the load of posting
        self.recipe_payload = self.get_recipe(1)        
        
    def get_recipe(self, recipe_index):    
        recipe = dummy_recipes[recipe_index]
        recipe_payload = {"recipe_name": recipe['name'],
                          "user_id":self.user_id,
                          "likes_count": 0,
                          "user_name": self.user_name,
                          "images":['https://storage.googleapis.com/up_food_pics/one-pot-cajun-pasta.jpg'],
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
            ingredients_imgs.append('https://storage.googleapis.com/up_food_pics/artichokes.png')
            ingredients.append(ig['material']['name'])
            
        recipe_payload.update({'ingredients':ingredients,
                               'ingredients_imgs':ingredients_imgs,
                               'ingredients_quant':ingredients_quant,
                               'ingredients_metric':ingredients_metric
                              })
        return recipe_payload
 
    @task
    def add_recipe_task(self):
        header = {'Content-Type':'application/json'}
        header.update({'auth_token':self.login_token})
        res = self.client.post('/recipes', data=json.dumps(self.recipe_payload), 
                               headers=header)            

    @task
    def get_recipe_task(self):
        header = {'Content-Type':'application/json'}
        header.update({'auth_token':self.login_token})
        res = self.client.get('/recipes/%s' %self.recipe_id, headers=header)
        
class UggiPuggiLocust(HttpLocust):
    task_set = UggiPuggiTaskSet
