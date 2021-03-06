# -*- coding: utf-8 -*-

from __future__ import absolute_import
import re
import time
import json
import os, sys
import unittest
import requests
import subprocess
from falcon import testing

sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))

#from uggipuggi.tests import get_test_uggipuggi
from uggipuggi.tests.restapi_utils import curl_request
from uggipuggi.tests.utils.dummy_data import users_gcs_base, food_gcs_base, users as dummy_users,\
                                             groups as dummy_groups, contacts as dummy_contacts,\
                                             following as dummy_following, recipes as dummy_recipes, feeds as dummy_feeds
from uggipuggi.tests.utils.dummy_data_utils import get_dummy_email, get_dummy_password,\
                                                   get_dummy_phone, get_dummy_display_name     


DEBUG_OTP = '999999'
class TestUggiPuggiRecipe(testing.TestBase):
    def setUp(self):
        try:
            uggipuggi_ip = os.environ['UGGIPUGGI_BACKEND_IP']
        except KeyError:
            ip_config = subprocess.run(["ifconfig", "docker_gwbridge"], stdout=subprocess.PIPE)
            ip_config = ip_config.stdout.decode('utf-8').split('\n')[1]
            uggipuggi_ip = re.findall(r".+ inet addr:([0-9.]+) .+", ip_config)[0]                        
            
        self.rest_api = 'http://%s/'%uggipuggi_ip
        self.verify_token = None
        self.login_token  = None
        self.test_user    = None
        count = 3000
        
        self.user_name = get_dummy_display_name(count)
        self.payload = {
                        "phone": get_dummy_phone(count),
                        "country_code": "IN",
                       }
        header = {'Content-Type':'application/json'}
        res = requests.post(self.rest_api + '/register', 
                            data=json.dumps(self.payload), 
                            headers=header)
        self.verify_token = json.loads(res.content.decode('utf-8'))['auth_token']
        header.update({'auth_token': self.verify_token})
        res = requests.post(self.rest_api + '/verify', 
                            data=json.dumps({'code':DEBUG_OTP}), 
                            headers=header)
        
        print('=========================')
        print(res.content.decode('utf-8'))
        res_dict = json.loads(res.content.decode('utf-8'))
        self.login_token = res_dict['auth_token']
        self.user_id     = res_dict['user_identifier']

        here = os.path.dirname(os.path.realpath(__file__))                        
        filepath = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'image.jpg')
        user_image = open(filepath, 'rb')

        header = {'auth_token':self.login_token}
        res = requests.put(self.rest_api + '/users/%s' %self.user_id,
                           files={'display_pic':('image.jpg', user_image, 'image/jpeg')}, 
                           data={'display_name': 'random_name'},
                           headers=header)
        user_image.close()
        self.assertEqual(200, res.status_code)
    
    def get_recipe(self, recipe_index):    
        recipe = dummy_recipes[recipe_index]
        recipe_payload = {"recipe_name": recipe['name'],
                          "expose_level": 1,
                          "category": 1,
                          "description": "This is a very easy and awesome dish. My family love this a lot!"
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
            ingredients.append(ig['material']['name'])
            
        recipe_payload.update({'ingredients':ingredients,
                               'ingredients_quant':ingredients_quant,
                               'ingredients_metric':ingredients_metric
                              })
        return recipe_payload
    
    def test_a_recipe(self):
        self.recipe_id = None
        first_recipe_payload = self.get_recipe(0)
        here = os.path.dirname(os.path.realpath(__file__))                        
        filepath = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'pasta.jpg')
        recipe_image = open(filepath, 'rb')
        
        header = {'auth_token':self.login_token}
        print (first_recipe_payload)
        res = requests.post(self.rest_api + '/recipes',
                            files={'images': ('pasta.jpg', recipe_image, 'image/jpeg')},
                            data=first_recipe_payload,
                            headers=header)
        recipe_image.close()
        print (res.text)
        self.assertEqual(201, res.status_code)
        self.assertTrue('recipe_id' in json.loads(res.content.decode('utf-8')))
        if 'recipe_id' in json.loads(res.content.decode('utf-8')):
            self.recipe_id = json.loads(res.content.decode('utf-8'))['recipe_id']
            print ("Recipe id :")
            print (self.recipe_id)
            
        header.update({'Content-Type':'application/json'})
        res = requests.get(self.rest_api + '/recipes/%s' %self.recipe_id, headers=header)
        print (res.text)
        self.assertEqual(302, res.status_code)
        
        # Wrong recipe id
        res = requests.get(self.rest_api + '/recipes/%s' %self.recipe_id+'0', headers=header)
        self.assertEqual(400, res.status_code)
        
        # Lets like the recipe
        res = requests.post(self.rest_api + '/recipe_liked/%s' %self.recipe_id, 
                            data=json.dumps({'liked':True}), 
                            headers=header)
        print (res.text)
        self.assertTrue('likes_count' in json.loads(res.content.decode('utf-8')))
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, int(json.loads(res.text)['likes_count']))
        
        # Lets save the recipe
        res = requests.post(self.rest_api + '/recipe_saved/%s' %self.recipe_id, 
                            data=json.dumps({'saved':True}), 
                            headers=header)
        print (res.text)
        self.assertTrue('saves_count' in json.loads(res.content.decode('utf-8')))
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, int(json.loads(res.text)['saves_count']))        
        self.assertEqual(200, res.status_code)
        
        # Lets unlike the recipe
        res = requests.post(self.rest_api + '/recipe_liked/%s' %self.recipe_id, 
                            data=json.dumps({'liked':False}), 
                            headers=header)
        print (res.text)
        self.assertTrue('likes_count' in json.loads(res.content.decode('utf-8')))
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, int(json.loads(res.text)['likes_count']))        
        self.assertEqual(200, res.status_code)
        
        # Lets unsave the recipe
        res = requests.post(self.rest_api + '/recipe_saved/%s' %self.recipe_id, 
                            data=json.dumps({'saved':False}), 
                            headers=header)
        print (res.text)
        self.assertTrue('saves_count' in json.loads(res.content.decode('utf-8')))
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, int(json.loads(res.text)['saves_count']))        
        self.assertEqual(200, res.status_code)
        
        print ("++++++++++++++++++++++++++++++++++")
        header = {'Content-Type':'application/json'}
        header.update({'auth_token':self.login_token})
        res = requests.get(self.rest_api + '/recipes?category=1', headers=header)
        self.assertEqual(302, res.status_code)
        print(res.text)
        items = json.loads(res.text)['items']        
        self.assertEqual(1, len(items))
        print ("++++++++++++++++++++++++++++++++++")
        
        time.sleep(10)
        res = requests.get(self.rest_api + '/user_recipes/%s' %self.user_id, headers=header)
        res_json = json.loads(res.text)
        print (res_json)
        print(res.status_code)        
        
        self.assertTrue('fields' in res_json)
        self.assertTrue('items' in res_json)
        self.assertEqual(1, len(res_json['items']))
        # This is not a list but a string
        print(json.loads(res.content.decode('utf-8'))['items'][0])
        self.assertTrue('http://lh3.googleusercontent.com' in json.loads(res.content.decode('utf-8'))['items'][0][0])

        # Delete recipe
        res = requests.delete(self.rest_api + '/recipes/%s' %self.recipe_id,
                              headers=header)        
        self.assertEqual(200, res.status_code)
        # We deleted the recipe, so we should not find it now
        res = requests.get(self.rest_api + '/recipes/%s' %self.recipe_id, headers=header)
        self.assertEqual(400, res.status_code)        
        

if __name__ == '__main__':
    if 'logs' not in os.listdir(sys.path[0]):
        os.mkdir('logs')
    unittest.main()    