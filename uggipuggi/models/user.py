# -*- coding: utf-8 -*-

from __future__ import absolute_import
from mongoengine import Document, StringField, EmailField, IntField, DateTimeField,\
                        BooleanField, LongField, URLField, ListField, DictField

class Role(object):
    # defines all available roles for users
    # this will and should determine the access control permissions for each endpoint
    ADMIN = 9
    EMPLOYEE = 8
    OWNER = 4
    USER = 1

    ROLE_MAP = {
        ADMIN: 'admin',
        EMPLOYEE: 'employee',
        OWNER: 'recipe_owner',
        USER: 'user'
    }

    @staticmethod
    def get_role_type(role):
        return Role.ROLE_MAP.get(role, 'user')

class Subscription(object):
    # defines all available subscription for users
    # this will and should determine the access control permissions and features for each endpoint
    ADS = 10
    BUSINESS = 8
    PREMIUM = 4
    FREE = 1
    
    SUBSCRIPTION_MAP = {
        ADS: 'ads',
        BUSINESS: 'business',
        PREMIUM: 'premium',
        FREE: 'free',
    }

    @staticmethod
    def get_subscription_type(subscription):
        return Subscription.SUBSCRIPTION_MAP.get(subscription, 'free')

class User(Document):

    country_code    = StringField(required=True, min_length=2, max_length=2)  # follows ISO_3166-1
    phone           = StringField(required=True, unique=True)  # contact number
    
    role            = IntField(required=True, default=Role.USER)    
    phone_verified  = BooleanField(required=True, default=False)
    account_active  = BooleanField(required=True, default=False)
    public_profile  = BooleanField(required=True, default=False) # Public or private profile?
    app_platform    = StringField(required=True, default="android")
    subscription    = IntField(required=True, default=Subscription.FREE)
    
    # Not mandatory
    #phone_last_verified = DateTimeField(required=False)    
    phone_last_verified = StringField(required=False)    
    display_name    = StringField(required=False, min_length=4, max_length=20)
    email           = EmailField(required=False)  # No need to be unique  
    first_name      = StringField(required=False)
    last_name       = StringField(required=False)
    display_pic     = URLField(required=False)
    gender          = StringField(required=False, min_length=4, max_length=6)        
    facebook_id     = LongField(required=False)  # Facebook ID is numeric but can be pretty big
    twitter_id      = StringField(required=False)  # Twitter ID is alphanumeric
    instagram_id    = StringField(required=False)  # Instagram ID is alphanumeric
    # For Firebase Clound Messaging
    device_registration_id = StringField(required=False)    
    #groups          = DictField(required=False)
    #contacts        = DictField(required=False)
    #followers       = DictField(required=False) # Those who follow this user
    #following       = DictField(required=False) # Those this user follows
    searchable_by_display_name = BooleanField(required=False, default=False)    
    #online_status = IntField(required=False)

    @property
    def subscription_type(self):
        return Subscription.get_subscription_type(self.subscription)
    
    def subscription_satisfy(self, subscription):
        return self.subscription >= subscription
    
    @property
    def role_type(self):
        return Role.get_role_type(self.role)

    def role_satisfy(self, role):
        return self.role >= role

class Group(Document):
    group_name = StringField(required=True, max_length=25)
    admins     = DictField(required=True)
    members    = DictField(required=False)
    group_pic  = URLField(required=False)
    
    @property
    def creation_stamp(self):
        # Time created can be obtained from the object _id attribute
        # sort by field _id and you'll get documents in creation time order
        return self.id.generation_time
    
class VerifyPhone(Document):
    phone = StringField(required=True, unique=True)  # contact number
    otp   = StringField(required=True, min_length=4, max_length=6)

