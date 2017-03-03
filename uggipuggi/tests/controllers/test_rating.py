# -*- coding: utf-8 -*-

from __future__ import absolute_import
from falcon import testing
from uggipuggi.tests import get_test_uggipuggi, get_mock_auth_middleware
from uggipuggi.controllers import rating
from uggipuggi.models.recipe import Recipe
from uggipuggi.models.rating import RecipeRating
from uggipuggi.models.user import User
import json
import mock


class TestRatingWithSetup(testing.TestBase):

    def setup_common_resources_DB(self):
        self.recipes = [Recipe(name='a', description='desca'), 
                        Recipe(name='b', description='descb') 
                       ]
        for recipe in self.recipes:
            recipe.save()
            
        self.users = [
            User(first_name='Clarke', last_name='Kent', display_name='Superman', email='clarke@kent.com', role=1),
            User(first_name='Bruce', last_name='Wayne', display_name='Batman', email='bruce@wayne.com', role=9),
        ]
        for user in self.users:
            user.save()

    def tearDownDB(self):
        Recipe.objects.delete()
        User.objects.delete()
        RecipeRating.objects.delete()

class TestRatingCollectionGet(TestRatingWithSetup):

    def setUp(self):
        with mock.patch('uggipuggi.JWTAuthMiddleware', return_value=get_mock_auth_middleware()):
            self.api = get_test_uggipuggi().app

        self.resource = rating.Collection()
        self.api.add_route('/rating/recipes', self.resource)
        self.srmock = testing.StartResponseMock()

        self.setup_common_resources_DB()

        self.rating = [
            RecipeRating(user=self.users[0], recipe=self.recipes[0], rating=4.0),
            RecipeRating(user=self.users[1], recipe=self.recipes[1], rating=2.0),
            RecipeRating(user=self.users[0], recipe=self.recipes[1], rating=5.0)
        ]
        for r in self.ratings:
            r.save()

    def tearDown(self):
        self.tearDownDB()

    def test_on_get(self):
        tests = [
            {'query_string': '', 'expected': {"status": 400}},
            {'query_string': 'start=1limit=1', 'expected': {"status": 400}},
            {'query_string': 'user_id={}'.format(self.users[0].id), 'expected': {"status": 200, "count": 2}},
            {'query_string': 'user_id={}'.format(self.users[1].id), 'expected': {"status": 200, "count": 1}}
        ]
        for t in tests:
            res = self.simulate_request('/ratings/recipes',
                                        query_string=t['query_string'],
                                        method='GET',
                                        headers={'accept': 'application/json'})

            self.assertTrue(isinstance(res, list))
            body = json.loads(res[0])
            self.assertTrue(isinstance(body, dict))

            if t['expected']['status'] != 200:  # expected erroneous requests
                self.assertNotIn('count', body.keys())
                self.assertIn('title', body.keys())
                self.assertIn('description', body.keys())
                continue

            self.assertItemsEqual(["count", "items"], body.keys())
            want = t['expected']['count']
            got = body['count']
            self.assertEqual(got, want, "{}| got: {}, want: {}".format(t['query_string'], got, want))


class TestRatingItemGet(TestRatingWithSetup):

    def setUp(self):
        with mock.patch('uggipuggi.JWTAuthMiddleware', return_value=get_mock_auth_middleware()):
            self.api = get_test_uggipuggi().app

        self.resource = rating.Item()
        self.api.add_route('/ratings/recipes/{id}', self.resource)
        self.srmock = testing.StartResponseMock()

        self.setup_common_resources_DB()

        self.ratings = [
            RecipeRating(user=self.users[0], recipe=self.recipes[0], rating=4.0),
            RecipeRating(user=self.users[1], recipe=self.recipes[1], rating=2.0),
            RecipeRating(user=self.users[0], recipe=self.recipes[1], rating=5.0)
        ]
        for r in self.ratings:
            r.save()

    def tearDown(self):
        self.tearDownDB()

    def test_on_get(self):
        tests = [
            {'id': 'randomID', 'expected': {'status': 400}},
            {'id': self.recipes[0].id, 'expected': {'status': 200, 'count': 1}},
            {'id': self.recipes[1].id, 'expected': {'status': 200, 'count': 2}}
        ]

        for t in tests:
            res = self.simulate_request('/ratings/recipes/{}'.format(t['id']),
                                        method='GET',
                                        headers={'accept': 'application/json'})

            self.assertTrue(isinstance(res, list))
            body = json.loads(res[0])
            self.assertTrue(isinstance(body, dict))

            if t['expected']['status'] != 200:  # expected erroneous requests
                self.assertNotIn('count', body.keys())
                self.assertIn('title', body.keys())
                self.assertIn('description', body.keys())
                continue

            got = body['count']
            want = t['expected']['count']
            self.assertEqual(got, want, "{}| got: {}, want: {}".format(t['id'], got, want))


class TestRatingItemPost(TestRatingWithSetup):

    def setUp(self):
        with mock.patch('uggipuggi.JWTAuthMiddleware', return_value=get_mock_auth_middleware()):
            self.api = get_test_uggipuggi().app

        self.resource = rating.Item()
        self.api.add_route('/ratings/recipes/{id}', self.resource)
        self.srmock = testing.StartResponseMock()

        self.setup_common_resources_DB()

    def tearDown(self):
        self.tearDownDB()

    def test_on_post(self):
        tests = [
            {'id': 'randomRecipeID', 'data': json.dumps({'user_id': 'randomString', 'rating': 3.0}), 'expected': {'status': 400}},
            {'id': str(self.recipes[0].id), 'data': json.dumps({'user_id': 'randomString', 'rating': 3.0}), 'expected': {'status': 400}},
            {
                'id': str(self.recipes[0].id),
                'data': json.dumps({
                    'user_id': str(self.users[0].id),
                    'rating': 4.0
                }),
                'expected': {
                    'status': 200,
                    'body': {
                        'rating': 4.0,
                        'menu': {'$id': {'$oid': str(self.recipes[0].id)}, '$ref': 'menu'},
                        'user': {'$id': {'$oid': str(self.users[0].id)}, '$ref': 'user'}
                    }
                }
            }
        ]

        for t in tests:
            res = self.simulate_request('/ratings/recipes/{id}'.format(id=t['id']),
                                        body=t['data'],
                                        method='POST',
                                        headers={'Content-Type': 'application/json'})

            self.assertTrue(isinstance(res, list))
            body = json.loads(res[0])
            self.assertTrue(isinstance(body, dict))

            if t['expected']['status'] != 200:
                self.assertNotIn('count', body.keys())
                self.assertIn('title', body.keys())
                self.assertIn('description', body.keys())
                continue

            self.assertDictContainsSubset(t['expected']['body'], body, 'got: {}, want: {}'.format(body, t['expected']['body']))


# class TestRatingItemDelete(TestRatingWithSetup):
#
#     def setUp(self):
#         self.resource = rating.Item()
#         self.api = get_test_snakebite().app
#
#         self.api.add_route('/ratings/menus/{id}', self.resource)
#         self.srmock = testing.StartResponseMock()
#
#         self.setup_common_resources_DB()
#
#         self.ratings = [
#             MenuRating(user=self.users[0], menu=self.menus[0], rating=4.0),
#             MenuRating(user=self.users[1], menu=self.menus[1], rating=2.0),
#             MenuRating(user=self.users[0], menu=self.menus[1], rating=5.0)
#         ]
#         for r in self.ratings:
#             r.save()
#
#     def tearDown(self):
#         self.tearDownDB()
#
#     def test_on_delete(self):
#         tests = [
#             {'id': 'randomMenuID', 'query_string': 'user_id=random', 'expected': {"status": 400}},
#             {'id': str(self.menus[0].id), 'query_string': 'user_id={}'.format("random"), 'expected': {"status": 400}},
#             {'id': str(self.menus[0].id), 'query_string': 'user_id={}'.format(str(self.users[1].id)), 'expected': {"status": 200}},  # none found but we return 200
#             {'id': str(self.menus[1].id), 'query_string': 'user_id={}'.format(str(self.users[1].id)), 'expected': {"status": 200}}
#         ]
#
#         for t in tests:
#             res = self.simulate_request('/ratings/menus/{}'.format(t['id']),
#                                         query_string=t['query_string'],
#                                         method='DELETE',
#                                         headers={'Content-Type': 'application/json'})
#
#             self.assertTrue(isinstance(res, list))
#             body = json.loads(res[0])
#             self.assertTrue(isinstance(body, dict))
#
#             if t['expected']['status'] != 200:
#                 self.assertTrue(isinstance(body, dict))
#                 self.assertIn('title', body.keys())
#                 self.assertIn('description', body.keys())  # error
#
#             else:
#                 self.assertIsNone(body)
#
#         self.assertItemsEqual([], MenuRating.objects(menu=self.menus[1], user=self.users[1]))  # deleted
#         self.assertNotEqual([], MenuRating.objects(menu=self.menus[0], user=self.users[0]))  # not deleted
#         self.assertNotEqual([], MenuRating.objects(menu=self.menus[1], user=self.users[0]))  # not deleted
