# -*- coding: utf-8 -*-
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
