# -*- coding: utf-8 -*-

from __future__ import absolute_import
import re
import json
import os, sys
import unittest
import requests
import subprocess
from six import BytesIO
from falcon import testing
from requests_toolbelt.multipart.encoder import MultipartEncoder

sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))

from uggipuggi.tests import get_test_uggipuggi
from uggipuggi.tests.utils.dummy_data import users_gcs_base, food_gcs_base, users as dummy_users,\
                                             groups as dummy_groups, contacts as dummy_contacts,\
                                             following as dummy_following, recipes as dummy_recipes, feeds as dummy_feeds
from uggipuggi.tests.utils.dummy_data_utils import get_dummy_email, get_dummy_password,\
                                                   get_dummy_phone, get_dummy_display_name     

DEBUG_OTP = '999999'
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
        
        self.payload = {
                        "phone": get_dummy_phone(count),
                        "country_code": "IN",
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
                        'name': 'register_again_user_exists',
                        'desc': 'User already exists',
                        'payload': self.payload,
                        'expected': {'status': 200}
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
                        'payload': {'code':DEBUG_OTP},
                        'auth_token': self.verify_token,
                        'expected': {'status': 202}
                    },
                    {
                        'name': 'verify_phone_failure_wrong_otp',
                        'desc': 'OTP code failure',
                        'payload': {'code':'222222'},
                        'auth_token': self.verify_token,
                        'expected': {'status': 406}
                    },
                    {
                        'name': 'verify_phone_failure_wrong_auth_token',
                        'desc': 'Wrong auth token',
                        'payload': {'code':DEBUG_OTP},
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
                if test['expected']['status'] == 202:
                    self.assertTrue('auth_token' in json.loads(res.content.decode('utf-8')))
                    self.assertTrue('user_identifier' in json.loads(res.content.decode('utf-8')))
                    if 'auth_token' in json.loads(res.content.decode('utf-8')):
                        self.login_token = json.loads(res.content.decode('utf-8'))['auth_token']
                        print ("setting login token")
                    if 'user_identifier' in json.loads(res.content.decode('utf-8')):
                        self.test_user = json.loads(res.content.decode('utf-8'))['user_identifier']
                        
        filepath = os.path.join(os.path.dirname(os.path.dirname(here)), 'test_data', 'image.jpg')
        image = open(filepath, 'rb')
        tests = [
                    {
                        'name': 'verify_gcs_storage',
                        'desc': 'success',
                        'payload': {'display_pic':image},
                        'auth_token': self.verify_token,
                        'expected': {'status': 200}
                    },
                ]
        
        header = {'Content-Type':'multipart/form-data'}
        for test in tests:
            with self.subTest(name=test['name']):
                header.update({'auth_token':test['auth_token']})
                res = requests.put(self.rest_api + '/users/%s' %self.test_user, 
                                    files=test['payload'], 
                                    headers=header)
                self.assertEqual(test['expected']['status'], res.status_code)


if __name__ == '__main__':
    if 'logs' not in os.listdir(sys.path[0]):
        os.mkdir('logs')
    unittest.main()    