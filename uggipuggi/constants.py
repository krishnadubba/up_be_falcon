# -*- coding: utf-8 -*-

import sys

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

TWEET_CHAR_LENGTH = 1000
DEFAULT_USER_STATUS = 'Hi, I am using UggiPuggi'
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
MAX_USER_FEED_LENGTH = 150
MAX_USER_FEED_LOAD   = 50

RECIPE_CONCISE_VIEW_FIELDS = ('images', 'recipe_name', 'likes_count', 'description', 
                              'saves_count', 'comments_count', 'cook_time',
                              "author_avatar", "user_id", "author_display_name")
ACTIVITY_CONCISE_VIEW_FIELDS = ('images', 'recipe_name', 'likes_count', 'description', 
                                'comments_count', 'cook_time', 'recipe_id',
                                "author_avatar", "user_id", "author_display_name")

# REDIS namespaces
RECIPE        = 'recipe:'
ACTIVITY      = 'act:'
GROUP         = 'grp:'
GROUP_FEED    = 'grp_feed:'
GROUP_MEMBERS = 'grp_members:'
USER          = 'u:'
USER_FEED     = 'u_feed:'
USER_GROUPS   = 'u_grps:'
USER_RECIPES  = 'u_recipes:'
USER_PINNED   = 'u_pinned:'
USER_LIKED    = 'u_liked:'
USER_ACTIVITY = 'u_act:'
PUBLIC_RECIPES= 'p_recipes'
CONTACTS      = 'contacts:'
FOLLOWING     = 'following:'
FOLLOWERS     = 'followers:'
OTP           = 'otp:'
RECIPE_COMMENTORS   = 'recipe_commentors:'
ACTIVITY_COMMENTORS = 'act_commentors:'
USER_NOTIFICATION_FEED = 'u_notify_feed:'

# Google Cloud Storage stuff
FILE_EXT_MAP = {'jpg': 'image/jpeg', 'jpe': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png'}
IMG_STORE_PATH = '/images/'
GAE_IMG_SERVER = 'https://uggipuggi-dev.appspot.com/img_post'
GCS_USER_BUCKET = 'gcs_user_public_server_bucket_dev'
GCS_GROUP_BUCKET = 'gcs_group_public_server_bucket_dev'
GCS_RECIPE_BUCKET = 'gcs_recipe_public_server_bucket_dev'
GCS_ACTIVITY_BUCKET = 'gcs_activity_public_server_bucket_dev'
BACKEND_ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'bmp']
GCS_ALLOWED_EXTENSION = 'image/jpeg'