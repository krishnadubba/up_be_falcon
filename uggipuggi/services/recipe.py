from __future__ import absolute_import
from uggipuggi.models.recipe import Recipe
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


def get_recipe(recipe_id):
    try:
        return Recipe.objects.get(id=recipe_id)
    except (DoesNotExist, MultipleObjectsReturned, ValidationError):
        return None
