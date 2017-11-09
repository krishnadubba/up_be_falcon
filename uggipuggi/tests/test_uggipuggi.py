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
from uggipuggi.tests.utils.dummy_data import users_gcs_base, users as dummy_users,\
                                             groups as dummy_groups, contacts as dummy_contacts,\
                                             following as dummy_following
from uggipuggi.tests.utils.dummy_data_utils import get_dummy_email, get_dummy_password,\
                                                   get_dummy_phone, get_dummy_display_name     


class TestUggiPuggiAuthMiddleware(testing.TestBase):
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
        count = 0
        
        user = dummy_users[0]
        current_author_id = user['id']
        self.password = get_dummy_password(count)
        self.payload = {
                        "email": get_dummy_email(count),
                        "password": self.password,
                        "phone": get_dummy_phone(count),
                        "country_code": "IN",
                        "display_name": user['name'],
                        "gender": user['sex'],
                        "display_pic": users_gcs_base + user['avatar'].split('/')[-1],
                        }        

    def tearDown(self):
        header = {'Content-Type':'application/json'}
        header.update({'auth_token':self.login_token})
        res = requests.delete(self.rest_api + '/users/%s'%self.test_user,
                              headers=header)
        if res.status_code == 200:
            print ("Successful test tearDown")
        else:
            print ("Test tearDown failed!!!")
        
    def test_a_jwt_auth_middleware(self):
        print ('Starting register user tests ...')
        tests = [
                    {
                        'name': 'register_success',
                        'desc': 'success',
                        'payload': self.payload,
                        'expected': {'status': 200}
                    },
                    {
                        'name': 'register_failure_user_exists',
                        'desc': 'User already exists',
                        'payload': self.payload,
                        'expected': {'status': 401}
                    },
                ]
        
        header = {'Content-Type':'application/json'}
        for test in tests:
            with self.subTest(name=test['name']):
                res = requests.post(self.rest_api + '/register', 
                                  data=json.dumps(test['payload']), 
                                  headers=header)
                             
                self.assertEqual(test['expected']['status'], res.status_code)
                if test['expected']['status'] == 200:
                    self.assertTrue('auth_token' in json.loads(res.content.decode('utf-8')))
                    if 'auth_token' in json.loads(res.content.decode('utf-8')):
                        self.verify_token = json.loads(res.content.decode('utf-8'))['auth_token']
                        print ("setting verify token")
                        
        # Verify Phone
        print ('Starting verify phone tests ...')
        tests = [
                    {
                        'name': 'verify_phone_success',
                        'desc': 'success',
                        'payload': {'code':'9999'},
                        'auth_token': self.verify_token,
                        'expected': {'status': 202}
                    },
                    {
                        'name': 'verify_phone_failure_wrong_otp',
                        'desc': 'OTP code failure',
                        'payload': {'code':'2222'},
                        'auth_token': self.verify_token,
                        'expected': {'status': 406}
                    },
                    {
                        'name': 'verify_phone_failure_wrong_auth_token',
                        'desc': 'Wrong auth token',
                        'payload': {'code':'9999'},
                        'auth_token': self.verify_token + '0',
                        'expected': {'status': 401}
                    },                        
                ]
        
        header = {'Content-Type':'application/json'}            
        for test in tests:
            with self.subTest(name=test['name']):
                header.update({'auth_token':test['auth_token']})
                res = requests.post(self.rest_api + '/verify', 
                                  data=json.dumps(test['payload']), 
                                  headers=header)
                             
                self.assertEqual(test['expected']['status'], res.status_code)                

        # Login
        print ('Starting login user tests ...')
        tests = [
                    {
                        'name': 'login_success',
                        'desc': 'success',
                        'payload': {'email':self.payload["email"], "password":self.payload["password"]},
                        'expected': {'status': 202}
                    },
                    {
                        'name': 'login_failure_wrong_password',
                        'desc': 'Password did not match',
                        'payload': {'email':self.payload["email"], "password":self.payload["password"]+'0'},
                        'expected': {'status': 403}
                    },
                    {
                        'name': 'login_failure_wrong_useremail',
                        'desc': 'User does not exist',
                        'payload': {'email':self.payload["email"]+'0', "password":self.payload["password"]},
                        'expected': {'status': 401}
                    },                        
                ]
        
        header = {'Content-Type':'application/json'}            
        for test in tests:
            with self.subTest(name=test['name']):
                res = requests.post(self.rest_api + '/login', 
                                  data=json.dumps(test['payload']), 
                                  headers=header)
                             
                self.assertEqual(test['expected']['status'], res.status_code)
                if test['expected']['status'] == 202:
                    self.assertTrue('auth_token' in json.loads(res.content.decode('utf-8')))
                    self.assertTrue('user_identifier' in json.loads(res.content.decode('utf-8')))
                    if 'auth_token' in json.loads(res.content.decode('utf-8')):
                        self.login_token = json.loads(res.content.decode('utf-8'))['auth_token']
                        print ("setting login token")
                    if 'user_identifier' in json.loads(res.content.decode('utf-8')):
                        self.test_user = json.loads(res.content.decode('utf-8'))['user_identifier']

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
        count = 0
        users_map = {}
        for user in dummy_users:
            current_author_id = user['id']
            payload = {
                       "email": get_dummy_email(count),
                       "password": get_dummy_password(count),
                       "phone": get_dummy_phone(count),
                       "country_code": "IN",
                       "display_name": user['name'],
                       "gender": user['sex'],
                       'display_pic': users_gcs_base + user['avatar'].split('/')[-1]
                      }
            
            if 'public_profile' in user:
                payload.update({"public_profile":True})
                
            header = {'Content-Type':'application/json'}    
            users_map[current_author_id] = payload
            res = requests.post(self.rest_api + '/register', data=json.dumps(payload), 
                                headers=header)
            verify_token = json.loads(res.content.decode('utf-8'))['auth_token']
            
            header.update({'auth_token':verify_token})
            res = requests.post(self.rest_api + '/verify', data=json.dumps({'code':'9999'}), 
                                headers=header)
            
            header = {'Content-Type':'application/json'}
            res = requests.post(self.rest_api + '/login', data=json.dumps({'email':users_map[current_author_id]["email"], 
                                                                   "password":users_map[current_author_id]["password"]}), 
                                headers=header)
            
            login_token   = json.loads(res.content.decode('utf-8'))['auth_token']
            user_mongo_id = json.loads(res.content.decode('utf-8'))['user_identifier']
            users_map[current_author_id].update({'login_token':login_token})
            users_map[current_author_id].update({'user_id':user_mongo_id})
            
            count += 1
            
        header = {'Content-Type':'application/json'}    
        for group in dummy_groups:
            with self.subTest(name=group['group_name']):
                group_payload = {}
                group_payload['group_name'] = group['group_name']
                group_payload['group_pic'] = group['group_pic']
                login_token = users_map[group['admin']]['login_token']
                header.update({'auth_token':login_token})
                
                res = requests.post(self.rest_api + '/groups', data=json.dumps(group_payload), 
                                  headers=header)
            
                self.assertEqual(201, res.status_code)
                self.assertTrue('group_id' in json.loads(res.content.decode('utf-8')))
                
                group_id = json.loads(res.content.decode('utf-8'))['group_id']
                
                # First memeber is the admin
                member_payload = {}
                member_payload['member_id'] = []
                for member in group['members'][1:]:    
                    member_payload['member_id'].append(users_map[member]['user_id'])
                    
                res = requests.post(self.rest_api + '/groups/%s'%group_id, data=json.dumps(member_payload), 
                                    headers=header)
                self.assertEqual(200, res.status_code)
                
                res = requests.get(self.rest_api + '/groups/%s?members=True'%group_id, headers=header)
                self.assertEqual(302, res.status_code)
                self.assertTrue('members' in json.loads(res.content.decode('utf-8')))
                self.assertEqual(len(group['members']), len(json.loads(res.content.decode('utf-8'))['members']))
                
        for contact in dummy_contacts:
            with self.subTest(name=users_map[contact[0]]['user_id']):
                login_token = users_map[contact[0]]['login_token']
                header.update({'auth_token':login_token})
                contact_payload = {}
                contact_payload['contact_user_id'] = []
                # Lets provide empty param and test
                res = requests.post(self.rest_api + '/contacts/%s'%users_map[contact[0]]['user_id'], 
                                                  data=json.dumps(contact_payload), 
                                                  headers=header)                 
                self.assertEqual(400, res.status_code)
                
                # Now give some ids to add
                for cont in contact[1:]:        
                    contact_payload['contact_user_id'].append(users_map[cont]['user_id'])
                res = requests.post(self.rest_api + '/contacts/%s'%users_map[contact[0]]['user_id'], 
                                  data=json.dumps(contact_payload), 
                                  headers=header)
                self.assertEqual(200, res.status_code)
                
                # Lets provide wrong param and test
                contact_payload = {}
                contact_payload['contact_user_wrong_key'] = []
                res = requests.post(self.rest_api + '/contacts/%s'%users_map[contact[0]]['user_id'], 
                                  data=json.dumps(contact_payload), 
                                  headers=header)                
                self.assertEqual(400, res.status_code)
                                        
        for contact in dummy_following:
            login_token = users_map[contact[0]]['login_token']
            header.update({'auth_token':login_token})
            contact_payload = {}
            for cont in contact[1:]:
                with self.subTest(name=users_map[contact[0]]['user_id']+'::'+users_map[cont]['user_id']):
                    contact_payload = {}
                    contact_payload['follower_user_id'] = users_map[cont]['user_id']
                    res = requests.post(self.rest_api + '/following/%s'%users_map[contact[0]]['user_id'], 
                                        data=json.dumps(contact_payload), 
                                        headers=header)
                    if 'public_profile' in users_map[cont]:
                        self.assertEqual(200, res.status_code)
                    else:
                        self.assertEqual(403, res.status_code)
            
class TestMain(testing.TestBase):

    def setUp(self):
        test_uggipuggi = get_test_uggipuggi()
        self.api = test_uggipuggi.app
        self.config = test_uggipuggi.config
        self.db = test_uggipuggi.db

    def test_db(self):
        self.assertIsNotNone(self.db)

    def test_config(self):
        # list out important sections and options in config files that should be loaded
        tests = [
            {'section': 'cors', 'options': ['allowed_origins', 'allowed_headers']},
            {'section': 'mongodb', 'options': ['name', 'host', 'port']},
            {'section': 'logging', 'options': ['level']}
        ]

        for t in tests:
            section = t['section']
            for option in t['options']:
                self.assertIn(option, self.config[section])



if __name__ == '__main__':
    unittest.main()    