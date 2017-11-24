# -*- coding: utf-8 -*-

from __future__ import absolute_import
from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, StringField,\
                  EmailField, IntField, DateTimeField, BooleanField, URLField, ListField
from uggipuggi.constants import TWEET_CHAR_LENGTH

class Comment(EmbeddedDocument):
    user_id = StringField(required=True)
    content = StringField(required=True, max_length=TWEET_CHAR_LENGTH)
    
    @property
    def creation_stamp(self):
        # Time created can be obtained from the object _id attribute
        # sort by field _id and you'll get documents in creation time order
        return self.id.generation_time
    
class CookingActivity(Document):
    user_id      = StringField(required=True)
    user_name    = StringField(required=True)
    recipe_name  = StringField(required=True)
    recipe_id    = StringField(required=True)
    likes_count  = IntField(required=True, default=0)
    description  = StringField(max_length=TWEET_CHAR_LENGTH)
    images       = ListField(URLField())  # list of urls
    # If the recipe id is private recipe, then we give warning when sharing activity involving it
    recipients   = ListField(StringField(default='*'))  # list of peolpe allowed to see
    tags         = ListField()
    category     = StringField()    
    shares_count = IntField(default=0)
    prep_time    = IntField(default=15)    
    cook_time    = IntField(default=15)    
    comments     = ListField(EmbeddedDocumentField(Comment), required=False)    
    
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
    