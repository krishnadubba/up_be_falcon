# -*- coding: utf-8 -*-

from __future__ import absolute_import
import re
import json
import os, sys
import unittest
import requests
import subprocess
from falcon import testing

sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))

from uggipuggi.tests import get_test_uggipuggi
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
        count = 20000
        
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

    def get_recipe(self, recipe_index):    
        recipe = dummy_recipes[recipe_index]
        recipe_payload = {"recipe_name": recipe['name'],
                          "user_id":self.user_id,
                          "likes_count": 0,
                          "user_name": self.user_name,
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
                            files={'images': recipe_image},
                            data=first_recipe_payload,
                            headers=header)
        recipe_image.close()
        self.assertEqual(201, res.status_code)
        self.assertTrue('recipe_id' in json.loads(res.content.decode('utf-8')))
        if 'recipe_id' in json.loads(res.content.decode('utf-8')):
            self.recipe_id = json.loads(res.content.decode('utf-8'))['recipe_id']
            print ("Recipe id :")
            print (self.recipe_id)
        res = requests.get(self.rest_api + '/recipes/%s' %self.recipe_id, headers=header)
        self.assertEqual(302, res.status_code)
        # Wrong recipe id
        res = requests.get(self.rest_api + '/recipes/%s' %self.recipe_id+'0', headers=header)
        self.assertEqual(400, res.status_code)
        
        # Delete recipe
        #res = requests.delete(self.rest_api + '/recipes/%s'%self.recipe_id,
                              #headers=header)        
        #self.assertEqual(200, res.status_code)
        ## We deleted the recipe, so we should not find it now
        #res = requests.get(self.rest_api + '/recipes/%s' %self.recipe_id, headers=header)
        #self.assertEqual(400, res.status_code)        


if __name__ == '__main__':
    if 'logs' not in os.listdir(sys.path[0]):
        os.mkdir('logs')
    unittest.main()    