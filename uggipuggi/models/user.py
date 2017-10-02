# -*- coding: utf-8 -*-

from __future__ import absolute_import
import mongoengine as mongo


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

class User(mongo.DynamicDocument):

    first_name = mongo.StringField(required=False)
    last_name = mongo.StringField(required=False)
    display_name = mongo.StringField(required=True, min_length=5, max_length=20)
    email = mongo.EmailField(required=True, unique=True)
    role = mongo.IntField(required=True, default=Role.USER)
    facebook_id = mongo.LongField(required=False)  # Facebook ID is numeric but can be pretty big
    twitter_id = mongo.StringField(required=False)  # Twitter ID is alphanumeric
    instagram_id = mongo.StringField(required=False)  # Instagram ID is alphanumeric
    country_code = mongo.StringField(min_length=2, max_length=2, required=True)  # follows ISO_3166-1
    phone = mongo.StringField(required=True, unique=True)  # contact number
    password = mongo.StringField(required=True, min_length=8)
    pw_last_changed = mongo.DateTimeField(required=True)
    phone_verified  = mongo.BooleanField(required=True, default=False)
    account_active  = mongo.BooleanField(required=True, default=False)
    subscription = mongo.IntField(required=True, default=Subscription.FREE)
    #online_status = mongo.IntField(required=True)

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

class VerifyPhone(mongo.DynamicDocument):

    phone = mongo.StringField(required=True, unique=True)  # contact number
    otp = mongo.StringField(required=True, min_length=4, max_length=5)
