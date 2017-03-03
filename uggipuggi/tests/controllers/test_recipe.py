# -*- coding: utf-8 -*-

from __future__ import absolute_import
from falcon import testing
from uggipuggi.tests import get_test_uggipuggi, get_mock_auth_middleware
from uggipuggi.controllers import recipe
from uggipuggi.models.recipe import Recipe
import json
import mock


class TestRecipeCollectionGet(testing.TestBase):

    def setUp(self):
        with mock.patch('uggipuggi.JWTAuthMiddleware', return_value=get_mock_auth_middleware()):
            self.api = get_test_uggipuggi().app

        self.resource = recipe.Collection()
        self.api.add_route('/recipes', self.resource)
        self.srmock = testing.StartResponseMock()
        self.recipes = [
            Recipe(name='a', description='desc'),
            Recipe(name='b', description='description')
        ]
        for r in self.recipes:
            r.save()

    def tearDown(self):
        Recipe.objects.delete()

    def test_collection_on_get(self):

        tests = [
            {'query_string': '', 'expected': {"status": 200, "count": 2}},
            {'query_string': 'description=desc', 'expected': {"status": 200, "count": 2}},
            {'query_string': 'description=desc&limit=1', 'expected': {"status": 200, "count": 1}},
            {'query_string': 'description=desc&start=1&limit=2', 'expected': {"status": 200, "count": 1}},
            {'query_string': 'description=description', 'expected': {"status": 200, "count": 1}},
            {'query_string': 'name=c', 'expected': {"status": 200, "count": 0}},
            {'query_string': 'limit=1', 'expected': {"status": 200, "count": 1}},
            {'query_string': 'start=2&limit=1', 'expected': {"status": 200, "count": 0}},
            {'query_string': 'start=1limit=1', 'expected': {"status": 400}}
        ]
        for t in tests:
            res = self.simulate_request('/recipes',
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
            self.assertEqual(body['count'], t['expected']['count'], "{}".format(t['query_string']))


class TestRecipeCollectionPost(testing.TestBase):

    def setUp(self):
        with mock.patch('uggipuggi.JWTAuthMiddleware', return_value=get_mock_auth_middleware()):
            self.api = get_test_uggipuggi().app

        self.resource = recipe.Collection()
        self.api.add_route('/recipes', self.resource)
        self.srmock = testing.StartResponseMock()

    def get_mock_recipe(self, **kwargs):
        base_recipe = {
            "name": "KFC",
        }
        base_recipe.update(kwargs)
        return base_recipe

    def tearDown(self):
        Recipe.objects.delete()

    def test_collection_on_post(self):

        recipe1 = self.get_mock_recipe(name="First Kitchen")  
        recipe2 = self.get_mock_recipe()
        
        tests = [
            {
                'data': json.dumps(recipe1),
                'expected': {
                    "name": "First Kitchen",
                    "description": "",
                }
            },
            {
                'data': json.dumps(recipe2),
                'expected': {
                    "name": "KFC",
                    "description": "",
                }
            }
        ]

        for t in tests:
            res = self.simulate_request('/recipes',
                                        body=t['data'],
                                        method='POST',
                                        headers={'Content-Type': 'application/json'})

            self.assertTrue(isinstance(res, list))
            body = json.loads(res[0])
            self.assertTrue(isinstance(body, dict))
            self.assertDictContainsSubset(t['expected'], body)


class TestRestaurantItemGet(testing.TestBase):

    def setUp(self):
        with mock.patch('snakebite.JWTAuthMiddleware', return_value=get_mock_auth_middleware()):
            self.api = get_test_snakebite().app

        self.resource = restaurant.Item()
        self.api.add_route('/restaurants/{id}', self.resource)
        self.srmock = testing.StartResponseMock()

        restaurants = [
            {
                'name': 'a',
                'description': 'desc A',
                'email': 'a@b.com',
                'address': 'tokyo',
            },
            {
                'name': 'b',
                'description': 'desc B',
                'email': 'b@a.com',
                'address': 'kyoto',
            }
        ]
        self.restaurants = []
        for r in restaurants:
            rest = Restaurant(**r)
            rest.save()
            self.restaurants.append(rest)

    def tearDown(self):
        Restaurant.objects(id__in=[r.id for r in self.restaurants]).delete()

    def test_item_on_get(self):
        tests = [
            {
                'id': r.id,
                'expected': {
                    'status': 200,
                    'id': {
                        '_id': {
                            '$oid': str(r.id)
                        }
                    }
                }
            } for r in self.restaurants
        ]

        for t in tests:
            res = self.simulate_request('/restaurants/{}'.format(t['id']),
                                        method='GET',
                                        headers={'Content-Type': 'application/json'})

            self.assertTrue(isinstance(res, list))
            body = json.loads(res[0])
            self.assertTrue(isinstance(body, dict))

            if t['expected']['status'] != 200:
                self.assertIn('title', body.keys())
                self.assertIn('description', body.keys())  # error

            else:
                self.assertDictContainsSubset(t['expected']['id'], body)


class TestRestaurantItemDelete(testing.TestBase):

    def setUp(self):
        with mock.patch('snakebite.JWTAuthMiddleware', return_value=get_mock_auth_middleware()):
            self.api = get_test_snakebite().app

        self.resource = restaurant.Item()
        self.api.add_route('/restaurants/{id}', self.resource)
        self.srmock = testing.StartResponseMock()

        restaurants = [
            {
                'name': 'a',
                'description': 'desc A',
                'email': 'a@b.com',
                'address': 'tokyo',
            },
            {
                'name': 'b',
                'description': 'desc B',
                'email': 'b@a.com',
                'address': 'kyoto',
            }
        ]
        self.restaurants = []
        for r in restaurants:
            rest = Restaurant(**r)
            rest.save()
            self.restaurants.append(rest)

    def tearDown(self):
        Restaurant.objects(id__in=[r.id for r in self.restaurants]).delete()

    def test_item_on_get(self):
        tests = [
            {
                'id': r.id,
                'expected': {
                    'status': 200,
                    'id': {
                        '_id': {
                            '$oid': str(r.id)
                        }
                    }
                }
            } for r in self.restaurants
        ]

        # add next test to delete already deleted restaurant
        tests.append(
            {
                'id': self.restaurants[0].id,
                'expected': {
                    'status': 400
                }
            }
        )

        for t in tests:
            res = self.simulate_request('/restaurants/{}'.format(t['id']),
                                        method='DELETE',
                                        headers={'Content-Type': 'application/json'})

            self.assertTrue(isinstance(res, list))
            body = json.loads(res[0])

            if t['expected']['status'] != 200:
                self.assertTrue(isinstance(body, dict))
                self.assertIn('title', body.keys())
                self.assertIn('description', body.keys())  # error

            else:
                self.assertIsNone(body)


class TestRestaurantItemPut(testing.TestBase):

    def setUp(self):
        with mock.patch('snakebite.JWTAuthMiddleware', return_value=get_mock_auth_middleware()):
            self.api = get_test_snakebite().app

        self.resource = restaurant.Item()
        self.api.add_route('/restaurants/{id}', self.resource)
        self.srmock = testing.StartResponseMock()
        self.restaurant = None
        rst = Restaurant(
            name='a',
            description='desc',
            email='a@b.com',
            address='Asakusa, Taito-ku, Tokyo',
            geolocation=[139.79843, 35.712074]
        )

        self.restaurant = rst.save()

    def tearDown(self):
        Restaurant.objects.delete()

    def _get_restaurant_json(self):
        res = self.simulate_request('/restaurants/{}'.format(self.restaurant.id),
                                    method="GET",
                                    headers={'Content-Type': 'application/json'})
        return res[0]

    def test_item_on_put(self):

        original_restaurant_json = self._get_restaurant_json()
        edited_restaurant_json = json.loads(original_restaurant_json)
        edited_restaurant_json.update({'name': 'Test Name'})
        edited_restaurant_json = json.dumps(edited_restaurant_json)

        tests = [
            {
                'id': self.restaurant.id,
                'data': original_restaurant_json,
                'expected': {
                    'status': 200,
                    'body': json.loads(original_restaurant_json)
                }
            },
            {
                'id': self.restaurant.id,
                'data': edited_restaurant_json,
                'expected': {
                    'status': 200,
                    'body': json.loads(edited_restaurant_json)
                }
            },
            {
                'id': "randomID",
                'data': original_restaurant_json,
                'expected': {
                    'status': 400
                }
            }
        ]

        for t in tests:
            res = self.simulate_request('/restaurants/{}'.format(t['id']),
                                        body=t['data'],
                                        method='PUT',
                                        headers={'Content-Type': 'application/json'})

            self.assertTrue(isinstance(res, list))
            body = json.loads(res[0])
            self.assertTrue(isinstance(body, dict))

            if t['expected']['status'] != 200:
                self.assertIn('title', body.keys())
                self.assertIn('description', body.keys())  # error

            else:
                self.assertDictEqual(t['expected']['body'], body)
