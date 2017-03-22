from __future__ import absolute_import
from uggipuggi.models.user import User
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


def get_user(id_type, user_id):
    try:
        if id_type == 'email':
            return User.objects.get(email=user_id)
        if id_type == 'id':
            return User.objects.get(id=user_id)
    except (DoesNotExist, MultipleObjectsReturned, ValidationError):
        return None
