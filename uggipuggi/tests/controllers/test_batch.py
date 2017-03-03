# -*- coding: utf-8 -*-

from __future__ import absolute_import
from falcon import testing
from uggipuggi.tests import get_test_uggipuggi, get_mock_auth_middleware
from uggipuggi.controllers import batch
from uggipuggi.models.recipe import Recipe
import json
import mock


class TestBatchRecipeCollectionGet(testing.TestBase):

    def setUp(self):
        with mock.patch('uggipuggi.JWTAuthMiddleware', return_value=get_mock_auth_middleware()):
            self.api = get_test_uggipuggi().app

        self.resource = batch.RecipeCollection()
        self.api.add_route('/batch/recipes', self.resource)
        self.srmock = testing.StartResponseMock()

        recipes = [
            {
                'name': 'a',
                'description': 'desc A',
            },
            {
                'name': 'b',
                'description': 'desc B',
            }
        ]
        self.recipes = []
        for r in recipes:
            rest = Recipe(**r)
            rest.save()
            self.recipes.append(rest)

    def tearDown(self):
        Recipe.objects(id__in=[r.id for r in self.recipes]).delete()

    def test_on_get(self):

        tests = [
            {'query_string': '', 'expected': {'status': 400}},
            {'query_string': 'ids=', 'expected': {'status': 400}},
            {'query_string': 'ids=,,,,', 'expected': {'status': 400}},
            {'query_string': 'ids=invalid', 'expected': {'status': 400}},
            {'query_string': 'ids={}'.format(self.recipes[0].id), 'expected': {'status': 200, 'count': 1}},
            {'query_string': 'ids={}'.format(",".join([str(r.id) for r in self.recipes])), 'expected': {'status': 200, 'count': len(self.recipes)}},
            {'query_string': 'ids={}&start=ignored'.format(",".join([str(r.id) for r in self.recipes])), 'expected': {'status': 200, 'count': len(self.recipes)}}
        ]

        for t in tests:
            res = self.simulate_request('/batch/recipes',
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
            got = body['count']
            want = t['expected']['count']
            self.assertEqual(got, want, "{}| got: {}, want: {}".format(t['query_string'], got, want))
