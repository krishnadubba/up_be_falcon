# -*- coding: utf-8 -*-

from __future__ import absolute_import
import mongoengine as mongo
from uggipuggi.constants import TWEET_CHAR_LENGTH

class Recipe(mongo.DynamicDocument):
    name = mongo.StringField(required=True)
    #author = mongo.StringField(required=True)
    description = mongo.StringField(max_length=TWEET_CHAR_LENGTH)
    images = mongo.ListField(mongo.URLField())  # list of urls
    tags = mongo.ListField()
    category = mongo.StringField()
    steps = mongo.ListField(required=True)
    ingredients = mongo.ListField(required=True)
    ingredients_quant = mongo.ListField(required=True)
    ingredients_metric = mongo.ListField(required=True)
    rating_count = mongo.IntField(default=0)
    likes_count = mongo.IntField(default=0)
    shares_count = mongo.IntField(default=0)
    rating_total = mongo.FloatField(default=0)
    prep_time = mongo.IntField(default=0)    
    cook_time = mongo.IntField(default=0)    
    last_modified = mongo.DateTimeField()
    
    @property
    def rating(self):
        if self.rating_count < 1:
            return 0.00
        return float(self.rating_total / float(self.rating_count))
        
    @property
    def creation_stamp(self):
        # Time created can be obtained from the object _id attribute
        # sort by field _id and you'll get documents in creation time order
        return self.id.generation_time        
    
#class Ingredients(mongo.DynamicDocument):
    #recipe = mongo.ReferenceField(Recipe, dbref=True, reverse_delete_rule=mongo.CASCADE)
    #ingredients = mongo.ListField(required=True)
    
#class RecipeSteps(mongo.DynamicDocument):
    #recipe = mongo.ReferenceField(Recipe, dbref=True, reverse_delete_rule=mongo.CASCADE)
    #recipesteps = mongo.ListField(required=True)
    