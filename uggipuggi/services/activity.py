from __future__ import absolute_import
from uggipuggi.models.cooking_activity import CookingActivity
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


def get_activity(activity_id):
    try:
        return CookingActivity.objects.get(id=activity_id)
    except (DoesNotExist, MultipleObjectsReturned, ValidationError):
        return None
