# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
from uggipuggi.controllers.hooks import deserialize, serialize
from uggipuggi.models.recipe import Recipe
from uggipuggi.libs.error import HTTPBadRequest
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


logger = logging.getLogger(__name__)

class RecipeCollection(object):
    def __init__(self):
        pass

    def _try_get_recipe(self, id):
        try:
            return Recipe.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            raise HTTPBadRequest(title='Invalid Value', description='Invalid ID provided. {}'.format(e.message))

    @falcon.before(deserialize)
    @falcon.after(serialize)
    def on_get(self, req, res):
        query_params = req.params.get('query')

        # get IDs
        try:
            ids = query_params.pop('ids')
        except KeyError:
            raise HTTPBadRequest(title='Invalid Request',
                                 description='Missing ID parameter in URL query')

        # parse IDs
        ids = ids.split(',')
        recipes = []
        for id in ids:
            recipe = self._try_get_recipe(id)
            recipes.append(recipe)

        res.body = {'items': recipes, 'count': len(recipes)}