# -*- coding: utf-8 -*-

from __future__ import absolute_import
import mongoengine as mongo
from uggipuggi.models.user import User
from uggipuggi.models.recipe import Recipe


class RecipeRating(mongo.DynamicDocument):
    # TODO: add compound index on user and menu
    user = mongo.ReferenceField(User, dbref=True)
    recipe = mongo.ReferenceField(Recipe, dbref=True)
    rating = mongo.FloatField(min_value=0, max_value=5, default=0)  # current avg rating
