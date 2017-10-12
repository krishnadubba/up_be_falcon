# -*- coding: utf-8 -*-

from __future__ import absolute_import
import mongoengine as mongo
from uggipuggi.constants import TWEET_CHAR_LENGTH

class Comment(mongo.EmbeddedDocument):
    user_id = mongo.StringField(required=True)
    content = mongo.StringField(required=True, max_length=TWEET_CHAR_LENGTH)
    
    @property
    def creation_stamp(self):
        # Time created can be obtained from the object _id attribute
        # sort by field _id and you'll get documents in creation time order
        return self.id.generation_time
    
class CookingActivity(mongo.DynamicDocument):
    user_id      = mongo.StringField(required=True)
    recipe_id    = mongo.StringField(required=True)
    likes_count  = mongo.IntField(required=True, default=0)
    description  = mongo.StringField(max_length=TWEET_CHAR_LENGTH)
    images       = mongo.ListField(mongo.URLField())  # list of urls
    # If the recipe id is private recipe, then we give warning when sharing activity involving it
    recipients   = mongo.ListField(mongo.StringField(default='*'))  # list of peolpe allowed to see
    tags         = mongo.ListField()
    category     = mongo.StringField()    
    shares_count = mongo.IntField(default=0)
    prep_time    = mongo.IntField(default=15)    
    cook_time    = mongo.IntField(default=15)    
    activity_time_stamp = mongo.DateTimeField()
    comments     = mongo.ListField(mongo.EmbeddedDocumentField(Comment), 
                                   required=False)    
    
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
    