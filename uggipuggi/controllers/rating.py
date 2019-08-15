# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
from uggipuggi import constants
from uggipuggi.controllers.hooks import deserialize, serialize
from uggipuggi.controllers.schema.rating import RecipeRatingSchema
from uggipuggi.models.recipe import Recipe
from uggipuggi.models.rating import RecipeRating
from uggipuggi.models.user import User
from uggipuggi.libs.error import HTTPBadRequest
from uggipuggi.helpers.logs_metrics import init_logger, init_statsd
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


logger = init_logger()
statsd = init_statsd('up.controllers.rating')

# -------- BEFORE_HOOK functions
def deserialize_create(req, res, resource):
    deserialize(req, res, resource, schema=RecipeRatingSchema())

# -------- END functions


class Collection(object):
    def __init__(self):
        pass

    @falcon.before(deserialize)
    @falcon.after(serialize)
    @statsd.timer('get_user_given_ratings_get')
    def on_get(self, req, res):
        """
        Search for user's Recipe ratings based on supplied user
        Only allows for searching by user
        """
        statsd.incr('get_user_given_rating.invocations')
        query_params = req.params.get('query')

        try:
            # get pagination limits
            start = int(query_params.pop('start', 0))
            limit = int(query_params.pop('limit', constants.PAGE_LIMIT))
            end = start + limit

        except ValueError as e:
            raise HTTPBadRequest(title='Invalid Value',
                                 description='Invalid arguments in URL query:\n{}'.format(e.message))

        user_id = query_params.pop('user_id', None)
        if not user_id:
            raise HTTPBadRequest(title='Invalid Request',
                                 description='Please supply a user ID in the query params')

        user = User.objects.get(id=user_id)
        updated_params = {'__raw__': {'user.$id': user.id}}

        ratings = RecipeRating.objects(**updated_params)[start:end]
        res.body = {'items': ratings, 'count': len(ratings)}
        statsd.incr('user_given_ratings.invocations')                


class Item(object):
    def __init__(self):
        pass

    def _try_get_recipe(self, id):
        try:
            return Recipe.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            raise HTTPBadRequest(title='Invalid Value', description='Invalid ID provided. {}'.format(e.message))

    @falcon.before(deserialize)
    @falcon.after(serialize)
    @statsd.timer('get_recipe_ratings_get')             
    def on_get(self, req, res, id):
        statsd.incr('recipe_rating.invocations')
        recipe = self._try_get_recipe(id)
        ratings = RecipeRating.objects(recipe=recipe)
        res.body = {'items': ratings, 'count': len(ratings)}
        statsd.incr('get_recipe_ratings.invocations')
        
    @falcon.before(deserialize_create)
    @falcon.after(serialize)
    @statsd.timer('give_rating_get')            
    def on_post(self, req, res, id):
        statsd.incr('post_recipe_rating.invocations')
        recipe = self._try_get_recipe(id)

        data = req.params.get('body')
        try:
            user = User.objects.get(id=data['user_id'])
        except (ValidationError, DoesNotExist, MultipleObjectsReturned):
            raise HTTPBadRequest(title='Invalid Request', description='Please supply a valid menu ID')

        # update menu ratings
        recipe.rating_count += 1
        recipe.rating_total += data['rating']

        # create a new menu rating instance
        rating = RecipeRating(recipe=recipe, user=user, rating=data['rating'])

        recipe.save()
        rating.save()

        rating = RecipeRating.objects.get(id=rating.id)
        res.body = rating
        statsd.incr('give_rating.invocations')

    @falcon.before(deserialize)
    @falcon.after(serialize)
    @statsd.timer('delete_rating_delete')
    def on_delete(self, req, res, id):
        statsd.incr('delete_recipe_rating.invocations')
        recipe = self._try_get_recipe(id)
        query_params = req.params.get('query')
        user_id = query_params.get('user_id')

        if not user_id:
            raise HTTPBadRequest(title='Invalid Request',
                                 description='Please supply a user ID in the query params')

        try:
            user = User.objects.get(id=user_id)
            RecipeRating.objects(recipe=recipe, user=user).delete()
            statsd.incr('delete_rating.invocations')

        except (ValidationError, DoesNotExist):
            raise HTTPBadRequest(title='Invalid Value', description='Invalid user or menu ID provided')
