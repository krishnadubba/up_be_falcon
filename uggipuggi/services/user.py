from __future__ import absolute_import
from uggipuggi.models.user import User, VerifyPhone
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


def get_user(id_type, user_id, verify=False):
    # If we are not verifying user phone
    if not verify:
        try:
            if id_type == 'email':
                return User.objects.get(email=user_id)
            elif id_type == 'id':
                return User.objects.get(id=user_id)
            elif id_type == 'phone':
                return User.objects.get(phone=user_id)
            else:
                return None
        except (DoesNotExist, MultipleObjectsReturned, ValidationError):
            return None
    else:
        # If we are verifying user phone, we use VerifyUser database
        try:
            if id_type == 'phone':
                return VerifyPhone.objects.get(phone=user_id)
            else:
                return None
        except (DoesNotExist, MultipleObjectsReturned, ValidationError):
            return None        
