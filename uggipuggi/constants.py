# -*- coding: utf-8 -*-

import sys

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

TWEET_CHAR_LENGTH = 1000
DEFAULT_USER_STATUS = 'Hi, I am using UggiPuggi'
#INTEGER_MAX = sys.maxint - 1
INTEGER_MAX = sys.maxsize - 1

PAGE_LIMIT = 20

MAX_TOKEN_AGE = 86400
GCLOUD_SERVICE_CREDS='/home/krishna/gcloud_credentials/uggipuggi-a17b68a1ad89.json'
FCM_SERVER_KEY = 'AAAAzPk-Tf4:APA91bGwttdFLH671-48ekIwFNW2htVppUH0qorLPxNEUNAQC_XtOcTDG2I2hzqn3p6JQ0wySadD_AV32agw35xYVXukCYsUQAv6gnf5xvdJhnQRZS_uZJq65V4hQv8jpI3Hp57FPCnu'

# Token valid for 90 days

OTP_LENGTH = 6
TOKEN_EXPIRATION_SECS = 7776000
VERIFY_PHONE_TOKEN_EXPIRATION_SECS = 3600

AUTH_SERVER_NAME = "bouncer"
AUTH_HEADER_USER_ID = "X-Gobbl-User-ID"
AUTH_SHARED_SECRET_ENV = "DUBBA_SECRET"

# REDIS constants 
MAX_USER_FEED_LENGTH = 500
MAX_USER_FEED_LOAD   = 50

# REDIS namespaces
RECIPE        = 'recipe:'
ACTIVITY      = 'activity:'
GROUP         = 'group:'
GROUP_MEMBERS = 'group_members:'
USER_GROUPS   = 'user_groups:'
CONTACTS      = 'contacts:'
FOLLOWING     = 'following:'
FOLLOWERS     = 'followers:'
USER_FEED     = 'user_feed:'
USER          = 'user:'
OTP           = 'otp:'
USER_NOTIFICATION_FEED = 'user_notification_feed:'
RECIPE_COMMENTORS = 'recipe_commentors:'

# Google Cloud Storage stuff
GCS_USER_BUCKET = 'gcs_user_public_server_bucket'
GCS_GROUP_BUCKET = 'gcs_group_public_server_bucket'
GCS_RECIPE_BUCKET = 'gcs_recipe_public_server_bucket'
GCS_ACTIVITY_BUCKET = 'gcs_activity_public_server_bucket'
BACKEND_ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'bmp']
GCS_ALLOWED_EXTENSION = 'image/jpeg'