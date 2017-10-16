# -*- coding: utf-8 -*-

import sys

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

TWEET_CHAR_LENGTH = 1000
#INTEGER_MAX = sys.maxint - 1
INTEGER_MAX = sys.maxsize - 1

PAGE_LIMIT = 20

MAX_TOKEN_AGE = 86400

# Token valid for 90 days
TOKEN_EXPIRATION_SECS = 7776000
VERIFY_PHONE_TOKEN_EXPIRATION_SECS = 86400

AUTH_SERVER_NAME = "bouncer"
AUTH_HEADER_USER_ID = "X-Gobbl-User-ID"
AUTH_SHARED_SECRET_ENV = "DUBBA_SECRET"

# REDIS namespaces
GROUP         = 'group:'
GROUP_MEMBERS = 'group_members:'
USER_GROUPS   = 'user_groups:'
CONTACTS      = 'contacts:'
FOLLOWING     = 'following:'
FOLLOWERS     = 'followers:'
USER_FEED     = 'user_feed:'
RECIPE_COMMENTORS = 'recipe_commentors:'