# -*- coding: utf-8 -*-

from __future__ import absolute_import
from falcon import testing
from uggipuggi.models.recipe import Recipe


class TestMenu(testing.TestBase):

    def setUp(self):
        self.recipe = Recipe(**{
            'name': 'a',
            'description': 'desc'
        })

    def tearDown(self):
        Recipe.objects.delete()

    def test_init(self):

        for property, value in recipe.iteritems():
            self.assertEquals(getattr(recipe, property), value)
        self.assertEqual(recipe.rating, 0.00 if not recipe.rating_count else float(recipe.rating_total / recipe.rating_count))
