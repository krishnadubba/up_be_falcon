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
class TestUggiPuggiSocialNetwork(testing.TestBase):
    def setUp(self):
        try:
            uggipuggi_ip = os.environ['UGGIPUGGI_BACKEND_IP']
        except KeyError:
            ip_config = subprocess.run(["ifconfig", "docker_gwbridge"], stdout=subprocess.PIPE)
            ip_config = ip_config.stdout.decode('utf-8').split('\n')[1]
            uggipuggi_ip = re.findall(r".+ inet addr:([0-9.]+) .+", ip_config)[0]                        
            
        self.rest_api = 'http://%s/'%uggipuggi_ip
        
    def test_a_groups(self):
        count = 100
        users_map = {}
        recipe_map = {}
        activity_map = {}
        print ("===============================================================")
        print ()           
        print ('Starting social network tests: adding Users ...')
        print ()
        print ("===============================================================")                
        for user in dummy_users:
            current_author_id = user['id']
            payload = {
                       "phone": get_dummy_phone(count),
                       "country_code": "IN",
                      }
            
            if 'public_profile' in user:
                payload.update({"public_profile":True})
                
            header = {'Content-Type':'application/json'}    
            users_map[current_author_id] = payload
            users_map[current_author_id]['display_name'] = user['name']                        
            res = requests.post(self.rest_api + '/register', data=json.dumps(payload), 
                                headers=header)
            verify_token = json.loads(res.content.decode('utf-8'))['auth_token']
            
            header.update({'auth_token':verify_token})
            res = requests.post(self.rest_api + '/verify', data=json.dumps({'code':DEBUG_OTP}), 
                                headers=header)
            
            login_token   = json.loads(res.content.decode('utf-8'))['auth_token']
            user_mongo_id = json.loads(res.content.decode('utf-8'))['user_identifier']
            users_map[current_author_id].update({'login_token':login_token})
            users_map[current_author_id].update({'user_id':user_mongo_id})
            
            count += 1
            
        print ("===============================================================")
        print ()                   
        print ('Starting social network tests: Adding Contacts ...')                
        print ()
        print ("===============================================================")        
        for contact in dummy_contacts:
            with self.subTest(name=users_map[contact[0]]['user_id']):
                login_token = users_map[contact[0]]['login_token']
                header.update({'auth_token':login_token})
                contact_payload = {}
                contact_payload['contact_user_id'] = []
                # Lets provide empty param and test
                res = requests.put(self.rest_api + '/contacts/%s'%users_map[contact[0]]['user_id'], 
                                                  data=json.dumps(contact_payload), 
                                                  headers=header)                 
                self.assertEqual(400, res.status_code)
                                
                # Now give some phone numbers to add
                for cont in contact[1:]:        
                    contact_payload['contact_user_id'].append(users_map[cont]['phone'])
                    
                res = requests.put(self.rest_api + '/contacts/%s'%users_map[contact[0]]['user_id'], 
                                   data=json.dumps(contact_payload), 
                                   headers=header)
                self.assertEqual(200, res.status_code)
                
                phone_numbers = []
                for cont in contact[1:]:        
                    phone_numbers.append(users_map[cont]['phone'])
            
                res = requests.post(self.rest_api + '/get_userid', 
                                    data=json.dumps({'phone_numbers':phone_numbers}),
                                    headers=header)
                self.assertEqual(200, res.status_code)
                results = json.loads(res.content.decode('utf-8'))
                self.assertTrue('items' in results)
                self.assertTrue('count' in results)
                print(results['items'])
                
                # Lets provide wrong param and test
                contact_payload = {}
                contact_payload['contact_user_wrong_key'] = []
                res = requests.put(self.rest_api + '/contacts/%s'%users_map[contact[0]]['user_id'], 
                                  data=json.dumps(contact_payload), 
                                  headers=header)                
                self.assertEqual(400, res.status_code)
            
        print ("===============================================================")
        print ()               
        print ('Starting social network tests: addings groups ...')    
        print ()
        print ("===============================================================")                
        
        #header = {'Content-Type':'application/json'}
        for group in dummy_groups:
            with self.subTest(name=group['group_name']):
                group_payload = {}
                group_payload['group_name'] = group['group_name']
                group_payload['member_id'] = []
                # Lets add a couple of member first.
                for member in group['members'][:2]:    
                    group_payload['member_id'].append(users_map[member]['user_id'])
                
                login_token = users_map[group['admin']]['login_token']
                header = {'auth_token':login_token}
                # Content-Type header is automatically done by requests for multi-part
                here = os.path.dirname(os.path.realpath(__file__))
                filepath = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'group.png')
                group_image = open(filepath, 'rb')
                
                res = requests.post(self.rest_api + '/groups', 
                                    files={'group_pic': group_image},
                                    data=group_payload, 
                                    headers=header)
                group_image.close()
                self.assertEqual(201, res.status_code)
                self.assertTrue('group_id' in json.loads(res.content.decode('utf-8')))
                
                group_id = json.loads(res.content.decode('utf-8'))['group_id']
                
                header.update({'Content-Type':'application/json'})
                # Lets add some more members
                member_payload = {}
                member_payload['member_id'] = []
                for member in group['members'][2:]:    
                    member_payload['member_id'].append(users_map[member]['user_id'])
                    
                res = requests.post(self.rest_api + '/groups/%s'%group_id, data=json.dumps(member_payload), 
                                    headers=header)
                self.assertEqual(200, res.status_code)
                
                res = requests.get(self.rest_api + '/groups/%s?members=True'%group_id, headers=header)
                self.assertEqual(302, res.status_code)
                self.assertTrue('members' in json.loads(res.content.decode('utf-8')))
                # We need num_group_mems + 1 as admin is added seperately to the group members
                self.assertEqual(len(group['members']) + 1, len(json.loads(res.content.decode('utf-8'))['members']))                
        
        print ("===============================================================")                               
        print ()
        print ('Starting social network tests: adding Following ...')
        print ()
        print ("===============================================================")        
        for contact in dummy_following:
            login_token = users_map[contact[0]]['login_token']
            header.update({'auth_token':login_token})
            contact_payload = {}
            for cont in contact[1:]:
                with self.subTest(name=users_map[contact[0]]['user_id']+'::'+users_map[cont]['user_id']):
                    contact_payload = {}
                    contact_payload['public_user_id'] = users_map[cont]['user_id']
                    res = requests.put(self.rest_api + '/following/%s'%users_map[contact[0]]['user_id'], 
                                       data=json.dumps(contact_payload), 
                                       headers=header)
                    if 'public_profile' in users_map[cont]:
                        self.assertEqual(200, res.status_code)
                    else:
                        self.assertEqual(403, res.status_code)

        print ("===============================================================")
        print ()   
        print ('Starting social network tests: Adding Receipes ...')
        print ()
        print ("===============================================================")        
        for user in dummy_users:
            current_author_id = user['id']
            # Add all the recipes authored by this user
            for recipe in dummy_recipes:
                if recipe['author']['id'] != current_author_id:
                    continue
                with self.subTest(name=recipe['name']):
                    login_token = users_map[current_author_id]['login_token']
                    header = {'auth_token':login_token}
                    
                    recipe_payload = {"recipe_name": recipe['name'],
                                      "user_id": users_map[current_author_id]['user_id'],
                                      "likes_count": 0,
                                      "user_name": users_map[current_author_id]['display_name'],
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
                        #ingredients_imgs.append(food_gcs_base+ig['material']['image'].split('/')[-1])
                        ingredients.append(ig['material']['name'])
                        
                    recipe_payload.update({'ingredients':ingredients,
                                           #'ingredients_imgs':ingredients_imgs,
                                           'ingredients_quant':ingredients_quant,
                                           'ingredients_metric':ingredients_metric
                                           })                      
                    
                    recipe_map[recipe['id']] = recipe_payload                    
                    
                    here = os.path.dirname(os.path.realpath(__file__))                        
                    filepath = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'pasta.jpg')
                    recipe_image = open(filepath, 'rb')
                    
                    res = requests.post(self.rest_api + 'recipes', 
                                        data=recipe_payload,
                                        files={'images': recipe_image},
                                        headers=header)
                    recipe_image.close()
                    self.assertEqual(201, res.status_code)
                    result_dict = json.loads(res.content.decode('utf-8')) 
                    self.assertTrue('recipe_id' in result_dict)
                    if 'recipe_id' in result_dict:
                        self.recipe_id = result_dict['recipe_id']
                    recipe_map[recipe['id']].update({'recipe_id':result_dict['recipe_id']})
                    
                    res = requests.get(self.rest_api + '/recipes/%s' %self.recipe_id, headers=header)
                    self.assertEqual(302, res.status_code)
                    
                    # Wrong recipe id
                    res = requests.get(self.rest_api + '/recipes/%s' %self.recipe_id+'0', headers=header)
                    self.assertEqual(400, res.status_code)
                
        print ("===============================================================")
        print ()                   
        print ('Starting social network tests: Adding comments ...')            
        print ()
        print ("===============================================================")        
        for recipe in dummy_recipes:
            recipe_id = recipe_map[recipe['id']]['recipe_id']
            for com in recipe['reviews']:
                user_id     = users_map[com['author']['id']]['user_id']
                user_name   = users_map[com['author']['id']]['display_name']
                login_token = users_map[com['author']['id']]['login_token']
                header = {'Content-Type':'application/json'}
                header.update({'auth_token':login_token})                    
                with self.subTest(name=recipe_id+'::'+user_id):
                    comment = {}
                    comment['comment'] = {}                        
                    comment['comment']['user_id']   = user_id
                    comment['comment']['user_name'] = user_name
                    comment['comment']['content']   = com['content'] 
                    res = requests.put(self.rest_api + 'recipes/%s'%recipe_id, data=json.dumps(comment), 
                                       headers=header)
                    self.assertEqual(200, res.status_code)
                    
                    res = requests.put(self.rest_api + 'recipes/%s'%recipe_id+'0', data=json.dumps(comment), 
                                       headers=header)
                    self.assertEqual(400, res.status_code)
                    
                    comment = {}
                    comment['wrong_key'] = {}                        
                    comment['wrong_key']['user_id']   = user_id
                    comment['wrong_key']['user_name'] = user_name
                    comment['wrong_key']['content']   = com['content'] 
                    res = requests.put(self.rest_api + 'recipes/%s'%recipe_id, data=json.dumps(comment), 
                                       headers=header)
                    self.assertEqual(400, res.status_code)                    
                    
                    comment = {}
                    comment['comment'] = {}                        
                    comment['comment']['wrong_key_user_id'] = user_id
                    comment['comment']['user_name'] = user_name
                    comment['comment']['content']   = com['content'] 
                    res = requests.put(self.rest_api + 'recipes/%s'%recipe_id, data=json.dumps(comment), 
                                       headers=header)
                    self.assertEqual(400, res.status_code)                    
   
        print ("===============================================================")
        print ()   
        print ('Starting social network tests: Adding Activity ...')
        print ()
        print ("===============================================================")        
        for feed in dummy_feeds:
            user_mongo_id   = users_map[feed['creator']['id']]['user_id']
            recipe_mongo_id = recipe_map[feed['recipe']['id']]['recipe_id']            
            with self.subTest(name=recipe_mongo_id+'::'+user_mongo_id):
                activity_payload = {"recipe_id": recipe_mongo_id,
                                    "recipe_name" : recipe_map[feed['recipe']['id']]['recipe_name'],
                                    "user_id": user_mongo_id,
                                    "user_name": users_map[feed['creator']['id']]['display_name'],
                                    "likes_count": 0,
                                    }
                here = os.path.dirname(os.path.realpath(__file__))                        
                filepath = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'pasta.jpg')
                activity_image = open(filepath, 'rb')
                
                header = {'auth_token':users_map[feed['creator']['id']]['login_token']}
                res = requests.post(self.rest_api + 'activity', 
                                    data=activity_payload, 
                                    files={'images': activity_image},
                                    headers=header)
                activity_image.close()
                
                self.assertEqual(201, res.status_code)
                result_dict = json.loads(res.content.decode('utf-8')) 
                self.assertTrue('activity_id' in result_dict)                

                activity_payload.update({'activity_id':result_dict['activity_id']})
                activity_map[feed['id']] = activity_payload   
            
                activity_Q_payload = {}
                res = requests.get(self.rest_api + 'activity', 
                                   params=activity_Q_payload, 
                                   headers=header)
                self.assertEqual(302, res.status_code)
                results = json.loads(res.content.decode('utf-8'))['items']   
                         
        print ("===============================================================")
        print ()
        print ('Starting social network tests: deleting from following list ...')
        print ()
        print ("===============================================================")                
        # Delete the members from user's following list
        header = {'Content-Type':'application/json'}    
        for contact in dummy_following:
            login_token = users_map[contact[0]]['login_token']
            header.update({'auth_token':login_token})
            contact_payload = {}
            for cont in contact[1:]:
                # We can only delete public users from following list (bcoz the list has only public profiles
                # as you can only follow public profiles)
                if 'public_profile' in users_map[cont]:
                    with self.subTest(name=users_map[contact[0]]['user_id']+'::'+users_map[cont]['user_id']):
                        contact_payload = {}
                        # This time 'public_user_id' is a list (user can delete many in one go)
                        contact_payload['public_user_id'] = [users_map[cont]['user_id']]
                        res = requests.post(self.rest_api + '/following/%s'%users_map[contact[0]]['user_id'], 
                                            data=json.dumps(contact_payload), 
                                            headers=header)
                        self.assertEqual(200, res.status_code)                        
         
        print ("===============================================================")
        print ()   
        print ('Starting social network tests: Testing Feeds ...')
        print ()
        print ("===============================================================")         
        user_mongo_id = users_map['U0016']['user_id']
        login_token   = users_map['U0016']['login_token']
        header = {'Content-Type':'application/json'}
        header.update({'auth_token':login_token})
    
        res = requests.get(self.rest_api + 'feed/%s'%user_mongo_id, headers=header)
        print('Response:')
        print(res.status_code)
        print(res.text)            

if __name__ == '__main__':
    if 'logs' not in os.listdir(sys.path[0]):
        os.mkdir('logs')
    unittest.main()    