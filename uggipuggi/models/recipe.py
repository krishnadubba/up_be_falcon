# -*- coding: utf-8 -*-

from __future__ import absolute_import
from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, StringField, EmailField,\
                 IntField, DateTimeField, BooleanField, LongField, FloatField, URLField, ListField
from uggipuggi.constants import TWEET_CHAR_LENGTH

class ExposeLevel(object):
    # defines all available roles for users
    # this will and should determine the access control permissions for each endpoint
    PRIVATE = 10
    FRIENDS = 5
    PUBLIC  = 1
    
    EXPOSE_MAP = {
        PRIVATE: 'private',
        FRIENDS: 'friends',
        PUBLIC : 'public',
    }

    @staticmethod
    def get_expose_level(expose):
        return ExposeLevel.EXPOSE_MAP.get(expose_level, 'private')
    
class Comment(EmbeddedDocument):
    user_id   = StringField(required=True)
    user_name = StringField(required=True)
    content   = StringField(required=True, max_length=TWEET_CHAR_LENGTH)
    
    @property
    def creation_stamp(self):
        # Time created can be obtained from the object _id attribute
        # sort by field _id and you'll get documents in creation time order
        return self.id.generation_time
    
class Recipe(Document):
    recipe_name        = StringField(required=True)
    user_id            = StringField(required=True) #User phone number is used to identify owner
    user_name          = StringField(required=True) #User display name
    steps              = ListField(required=True)
    likes_count        = IntField(required=True, default=0)
    ingredients        = ListField(required=True) #Ingredients names
    ingredients_quant  = ListField(required=True) 
    ingredients_metric = ListField(required=True)
    # This should be private by default
    expose_level       = IntField(required=True, default=ExposeLevel.FRIENDS)
    
    video_url          = URLField(required=False)
    ingredients_imgs   = ListField(URLField()) # list of urls of ingredients images
    ingredients_ids    = ListField(required=False) #Ingredients ids        
    tips               = ListField(required=False)    
    description        = StringField(required=False, max_length=TWEET_CHAR_LENGTH)
    images             = ListField(URLField())  # list of urls
    tags               = ListField(required=False)
    category           = ListField(required=False)         # Should this be a class?
    rating_count       = IntField(required=False, default=0)
    shares_count       = IntField(required=False, default=0)
    rating_total       = FloatField(required=False, default=0.0)
    prep_time          = IntField(required=False, default=15) # In minutes   
    cook_time          = IntField(required=False, default=15) # In minutes   
    last_modified      = DateTimeField(required=False)
    comments           = ListField(EmbeddedDocumentField(Comment), required=False)
    
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
    