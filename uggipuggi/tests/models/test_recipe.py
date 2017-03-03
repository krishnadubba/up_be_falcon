# -*- coding: utf-8 -*-

from __future__ import absolute_import
from falcon import testing
from uggipuggi.models.recipe import Recipe


class TestRestaurant(testing.TestBase):

    def setUp(self):
        self.recipes = [
            {
                'dict': {
                    'name': 'a',
                    'description': 'desc A',
                }
            },
            {
                'dict': {
                    'name': 'b',
                    'description': 'desc B',
                }
            }
        ]

    def tearDown(self):
        Recipe.objects.delete()

    def test_init(self):

        for r in self.recipes:
            attributes = r['dict']
            recipe = Recipe(**attributes)

            for property, value in attributes.iteritems():
                self.assertEquals(getattr(recipe, property), value)

    def test_save(self):
        for i, r in enumerate(self.recipes):
            attributes = r['dict']
            recipe = Recipe(**attributes)
            recipe.save()
            self.assertEquals(len(Recipe.objects), i + 1)

    def test_remove(self):
        Recipe.objects(name__in=['a', 'b']).delete()
        self.assertEquals(len(Recipe.objects), 0)
