# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
from uggipuggi import constants
from uggipuggi.controllers.hooks import deserialize, serialize
from uggipuggi.controllers.schema.recipe import RecipeSchema, RecipeCreateSchema
from uggipuggi.models.recipe import Recipe
from uggipuggi.libs.error import HTTPBadRequest
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


# -------- BEFORE_HOOK functions
def deserialize_create(req, res, resource, kwargs):
    deserialize(req, res, resource, schema=RecipeSchema())

def deserialize_update(req, res, id, resource):
    deserialize(req, res, resource, schema=RecipeSchema())

# -------- END functions

logger = logging.getLogger(__name__)


class Collection(object):
    def __init__(self):
        pass

    @falcon.before(deserialize)
    @falcon.after(serialize)
    def on_get(self, req, res):
        query_params = req.params.get('query')

        try:
            # get pagination limits
            start = int(query_params.pop('start', 0))
            limit = int(query_params.pop('limit', constants.PAGE_LIMIT))
            end = start + limit

        except ValueError as e:
            raise HTTPBadRequest(title='Invalid Value',
                                 description='Invalid arguments in URL query:\n{}'.format(e.message))
        # custom filters
        # temp dict for updating query filters
        updated_params = {}

        for item in ['name', 'description']:
            if item in query_params:
                item_val = query_params.pop(item)
                updated_params['{}__icontains'.format(item)] = item_val

        query_params.update(updated_params)  # update modified params for filtering

        recipes = Recipe.objects(**query_params)[start:end]

        res.body = {'items': recipes, 'count': len(recipes)}

    @falcon.before(deserialize_create)
    @falcon.after(serialize)
    def on_post(self, req, res):
        # save restaurants, and menus (if any)
        data = req.params.get('body')  # recipe data
        logger.debug(data)
        
        # save to DB
        recipe = Recipe(**data)
        recipe.save()
        
        # return Recipe
        recipe = Recipe.objects.get(id=recipe.id)
        res.body = recipe


class Item(object):
    def __init__(self):
        pass

    def _try_get_recipe(self, id):
        try:
            return Recipe.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            raise HTTPBadRequest(title='Invalid Value', description='Invalid ID provided. {}'.format(e.message))

    @falcon.after(serialize)
    def on_get(self, req, res, id):
        recipe = self._try_get_recipe(id)

    @falcon.after(serialize)
    def on_delete(self, req, res, id):
        recipe = self._try_get_recipe(id)
        recipe.delete()

    # TODO: handle PUT requests
    @falcon.before(deserialize_update)
    @falcon.after(serialize)
    def on_put(self, req, res, id):
        recipe = self._try_get_recipe(id)
        data = req.params.get('body')

        # save to DB
        for key, value in data.iteritems():
            setattr(recipe, key, value)
        recipe.save()

        recipe = Recipe.objects.get(id=id)
        res.body = recipe
