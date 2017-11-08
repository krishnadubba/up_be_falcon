# -*- coding: utf-8 -*-

from __future__ import absolute_import
import jwt
import json
import os, sys
import mock
import logging
import unittest
from datetime import datetime
from falcon import testing
from passlib.hash import bcrypt as crypt

sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))

from uggipuggi.tests import get_test_uggipuggi
from uggipuggi.tests.utils.dummy_data import users_gcs_base, users as dummy_users
from uggipuggi.tests.utils.dummy_data_utils import get_dummy_email, get_dummy_password,\
                                                  get_dummy_phone, get_dummy_display_name     
from uggipuggi import constants
from uggipuggi.models.user import User, Role
from uggipuggi.middlewares import auth_jwt


class TestMain(testing.TestBase):

    def setUp(self):
        logging.disable(logging.INFO)
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


#class TestCorsMiddlewares(testing.TestBase):

    #def test_cors(self):

        #def _prepare():
            #mock_cors_dict = {
                #'allowed_origins': 'http://benri.com:5000,http://google.com',
                #'allowed_headers': 'Content-Type',
                #'allowed_methods': 'GET,PUT,POST,DELETE,OPTIONS'
            #}

            #uggipuggi = get_test_uggipuggi()
            #uggipuggi.config = {'cors': mock_cors_dict}
            #return uggipuggi.cors_middleware()

        #cors_middleware = _prepare()
        #dummy = mock.Mock()
        #req = mock.Mock()

        #tests = [
            #{'origin': 'http://benri.com:5000', 'allowed': True},
            #{'origin': 'http://benri.com:6000', 'allowed': False},
            #{'origin': 'http://google.com', 'allowed': True},
            #{'origin': 'http://mylittlepony.com', 'allowed': False},
        #]

        #for t in tests:
            #req.get_header.return_value = t['origin']
            #res = mock.Mock()
            #res.headers = {}

            #def set_mock_header(dct):
                #res.headers.update(dct)

            #res.set_headers = set_mock_header
            #cors_middleware(req, res, dummy)

            #if t['allowed']:
                #self.assertIn('Access-Control-Allow-Origin', res.headers)
            #else:
                #self.assertNotIn('Access-Control-Allow-Origin', res.headers)


class TestAuthMiddleware(testing.TestBase):
    def setUp(self):
        self.api = get_test_uggipuggi().app
        self.api.add_route('/login', auth_jwt.LoginResource)
        self.srmock = testing.StartResponseMock()
        
        user = dummy_users[0]
        current_author_id = user['id']
        count = 1
        self.password = get_dummy_password(count)
        self.payload = {"email": get_dummy_email(count),
                   "password": crypt.encrypt(self.password),
                   "phone": get_dummy_phone(count),
                   "country_code": "IN",
                   "display_name": user['name'],
                   "gender": user['sex'],
                   "display_pic": users_gcs_base + user['avatar'].split('/')[-1],
                   "pw_last_changed": datetime.utcnow(),
                   "phone_verified": True,
                   "account_active": True                   
                  }        

        self.mongo_user = User(**self.payload)
        self.mongo_user.save()

    def tearDown(self):
        User.objects.delete()

    def test_jwt_auth_middleware_login(self):
        tests = [
            {
                'desc': 'success',
                'payload': {'email': self.payload["email"], "password":self.password},
                'expected': {'status': 202}
            },
            {
                  'desc': 'wrong email',
                  'payload': {'email': 'dummyemail@gmail.com', "password":self.password},
                  'expected': {'status': 401}
            },
            {
                  'desc': 'wrong password',
                  'payload': {'email': self.payload["email"], "password": 'dummypassword'},
                  'expected': {'status': 403}
            },
        ]
        for test in tests:
            payload = test.get('payload')
           
            res = self.simulate_request('/login',
                                        method='POST',
                                        body=json.dumps(payload),
                                        headers={'Content-Type':'application/json'})

            body = json.loads(res[0].decode('utf-8'))
            self.assertTrue(isinstance(body, dict))

            if test['expected']['status'] != 202:
                self.assertEqual(body['title'], "'Login Failed'")
            else:
                print (body)
                self.assertEqual(body, {'ok': True})
        
    #def test_jwt_auth_middleware(self):
        #tests = [
            #{
                #'desc': 'success',
                #'payload': {'sub': str(self.users[0].id), 'iss': constants.AUTH_SERVER_NAME, 'acl': 'admin'},
                #'secret': os.getenv(constants.AUTH_SHARED_SECRET_ENV),
                #'expected': {'status': 200}
            #},
            #{
                #'desc': 'missing jwt params',
                #'expected': {'status': 401}
            #},
            #{
                #'desc': 'wrong secret',
                #'payload': {'sub': str(self.users[0].id), 'iss': constants.AUTH_SERVER_NAME, 'acl': 'admin'},
                #'secret': 'hush hush',
                #'expected': {'status': 401}
            #},
            #{
                #'desc': 'wrong iss',
                #'payload': {'sub': str(self.users[0].id), 'iss': 'butler', 'acl': 'admin'},
                #'secret': os.getenv(constants.AUTH_SHARED_SECRET_ENV),
                #'expected': {'status': 401}
            #},
            #{
                #'desc': 'missing values',
                #'payload': {'iss': 'butler'},
                #'secret': os.getenv(constants.AUTH_SHARED_SECRET_ENV),
                #'expected': {'status': 401}
            #},
            #{
                #'desc': 'invalid user id',
                #'payload': {'sub': 'whosyourdaddy', 'iss': constants.AUTH_SERVER_NAME, 'acl': 'admin'},
                #'secret': os.getenv(constants.AUTH_SHARED_SECRET_ENV),
                #'expected': {'status': 401}
            #}
        #]

        #for test in tests:
            #payload = test.get('payload')
            #token = jwt.encode(payload, test['secret']) if payload else None
            #qs = 'token={}'.format(token) if token else None

            #res = self.simulate_request('/status',
                                        #query_string=qs,
                                        #method='GET',
                                        #headers={'accept': 'application/json'})

            #body = json.loads(res[0])
            #self.assertTrue(isinstance(body, dict))

            #if test['expected']['status'] != 200:
                #self.assertEqual(body['title'], "Authorization Failed")
            #else:
                #self.assertEqual(body, {'ok': True})


#class TestAuthMiddleware_old(testing.TestBase):
    #def setUp(self):
        #self.api = get_test_uggipuggi().app
        #self.resource = status.Status()
        #self.api.add_route('/status', self.resource)
        #self.srmock = testing.StartResponseMock()

        #users = [
            #User(first_name='Clarke', last_name='Kent', display_name='Clarke Kent', email='superman@gmail.com', role=Role.USER)
        #]
        #self.users = []
        #for user in users:
            #user.save()
            #self.users.append(user)

    #def tearDown(self):
        #User.objects.delete()

    #def test_jwt_auth_middleware(self):
        #tests = [
            #{
                #'desc': 'success',
                #'payload': {'sub': str(self.users[0].id), 'iss': constants.AUTH_SERVER_NAME, 'acl': 'admin'},
                #'secret': os.getenv(constants.AUTH_SHARED_SECRET_ENV),
                #'expected': {'status': 200}
            #},
            #{
                #'desc': 'missing jwt params',
                #'expected': {'status': 401}
            #},
            #{
                #'desc': 'wrong secret',
                #'payload': {'sub': str(self.users[0].id), 'iss': constants.AUTH_SERVER_NAME, 'acl': 'admin'},
                #'secret': 'hush hush',
                #'expected': {'status': 401}
            #},
            #{
                #'desc': 'wrong iss',
                #'payload': {'sub': str(self.users[0].id), 'iss': 'butler', 'acl': 'admin'},
                #'secret': os.getenv(constants.AUTH_SHARED_SECRET_ENV),
                #'expected': {'status': 401}
            #},
            #{
                #'desc': 'missing values',
                #'payload': {'iss': 'butler'},
                #'secret': os.getenv(constants.AUTH_SHARED_SECRET_ENV),
                #'expected': {'status': 401}
            #},
            #{
                #'desc': 'invalid user id',
                #'payload': {'sub': 'whosyourdaddy', 'iss': constants.AUTH_SERVER_NAME, 'acl': 'admin'},
                #'secret': os.getenv(constants.AUTH_SHARED_SECRET_ENV),
                #'expected': {'status': 401}
            #}
        #]

        #for test in tests:
            #payload = test.get('payload')
            #token = jwt.encode(payload, test['secret']) if payload else None
            #qs = 'token={}'.format(token) if token else None

            #res = self.simulate_request('/status',
                                        #query_string=qs,
                                        #method='GET',
                                        #headers={'accept': 'application/json'})

            #body = json.loads(res[0])
            #self.assertTrue(isinstance(body, dict))

            #if test['expected']['status'] != 200:
                #self.assertEqual(body['title'], "Authorization Failed")
            #else:
                #self.assertEqual(body, {'ok': True})

if __name__ == '__main__':
    unittest.main()    