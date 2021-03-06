# -*- coding: utf-8 -*-

from __future__ import absolute_import
from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, StringField, EmailField,\
                 IntField, DateTimeField, BooleanField, LongField, FloatField, URLField, ListField
from uggipuggi.constants import TWEET_CHAR_LENGTH
from uggipuggi.models import ExposeLevel

    
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
    user_id            = StringField(required=True) #User mongodb ID is used to identify owner
    steps              = ListField(required=True)
    ingredients        = ListField(required=True) #Ingredients names
    ingredients_quant  = ListField(required=True) 
    ingredients_metric = ListField(required=True)
    comments_disabled  = BooleanField(required=True, default=False)
    category           = IntField(required=True)     # Should this be a class?
    author_display_name = StringField(required=True, default='UggiPuggi User') #User display name
    author_avatar      = StringField(required=True, default="")
    item_type          = StringField(required=True, default="recipe")
    likes_count        = IntField(required=True, default=0)    
    comments_count     = IntField(required=True, default=0)
    saves_count        = IntField(required=True, default=0)
    prep_time          = IntField(required=True, default=15) # In minutes   
    cook_time          = IntField(required=True, default=15) # In minutes   
    description        = StringField(required=True, default="", max_length=TWEET_CHAR_LENGTH)
    
    # This should be FRIENDS by default if profile is not public
    # otherwise it should be public
    expose_level       = IntField(required=True, default=ExposeLevel.FRIENDS)
    ack_category       = IntField(required=True, default=0)
    ack_text           = StringField(required=False)
    
    generation_time    = StringField(required=False)
    video_url          = URLField(required=False)
    ingredients_imgs   = ListField(URLField()) # list of urls of ingredients images
    ingredients_ids    = ListField(required=False) #Ingredients ids        
    tips               = ListField(required=False)    
    images             = ListField(StringField())  # list of urls
    tags               = ListField(required=False)
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
    