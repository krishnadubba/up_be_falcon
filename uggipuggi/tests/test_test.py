# -*- coding: utf-8 -*-

from __future__ import absolute_import
from falcon import testing
import mock
import logging
import sys
import unittest
sys.path.append('/home/dubba/work/webdev/backends/up_be_falcon')

from uggipuggi.tests import get_test_uggipuggi
from uggipuggi import constants
from uggipuggi.models.user import User, Role
from uggipuggi.controllers import status
from uggipuggi.middlewares import auth_jwt
import jwt
import json
import os


class TestTest(testing.TestBase):

    def setUp(self):
        logging.disable(logging.INFO)
        test_uggipuggi = get_test_uggipuggi()
        self.api = test_uggipuggi.app
        self.config = test_uggipuggi.config
        self.db = test_uggipuggi.db
        
        self.resource = auth_jwt.Test()
        self.api.add_route('/test', self.resource)
        self.srmock = testing.StartResponseMock()

    def test_db(self):
        self.assertIsNotNone(self.db)

    def test_resource_test_on_get(self):
        res = self.simulate_request('/test',
                                    method='GET',
                                    headers={'accept': 'application/json'})        

        self.assertTrue(isinstance(res, list))
        body = json.loads(res[0].decode('utf-8'))
        print ('===================')
        print (res)
        print (body)
        self.assertTrue(isinstance(body, dict))

                
if __name__ == '__main__':
    unittest.main()                