import falcon
import jwt
import os
import time
import json
import plivo
import random
import string
import traceback

from random import randint
from bson import json_util, ObjectId
from datetime import datetime, timedelta
from passlib.hash import bcrypt as crypt

from uggipuggi.constants import OTP, OTP_LENGTH, USER, USER_RECIPES, USER_FEED,\
                                PUBLIC_RECIPES, SERVER_RUN_MODE
from uggipuggi.models.user import Role, User, VerifyPhone
from uggipuggi.controllers import Ping
from uggipuggi.middlewares.prometheus_middleware import PrometheusMiddleware
from uggipuggi.controllers.hooks import deserialize, serialize, supply_redis_conn
from uggipuggi.helpers.logs_metrics import init_logger, init_statsd, init_tracer
from uggipuggi.messaging.authentication_kafka_producers import kafka_verify_producer,\
                     kafka_register_producer, kafka_login_producer, kafka_logout_producer,\
                     kafka_forgotpassword_producer, kafka_passwordchange_producer


logger = init_logger()
statsd = init_statsd('up.middlewares.auth')

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return repr(randint(range_start, range_end))

DEFAULT_TOKEN_OPTS = {"name": "auth_token", "location": "header"}
SRC_PHONE_NUM = '00447901103131'

if not SERVER_RUN_MODE == 'DEBUG':
    sms_auth_id = os.environ["SMS_AUTH_ID"]
    sms_auth_token = os.environ["SMS_AUTH_TOKEN"]
    sms = plivo.RestAPI(sms_auth_id, sms_auth_token)

# role-based permission control
ACL_MAP = {
    '/images/+': {
        'get':  Role.USER,
    },    
    '/recipes': {
        'get':  Role.USER,
        'post': Role.USER
    },
    '/recipes/+': {
        'get' :   Role.USER,
        'put' :   Role.USER,
        'delete': Role.USER
    },
    '/activity': {
        'get' : Role.USER,
        'post': Role.USER
    },
    '/activity/+': {
        'get':    Role.USER,
        'put':    Role.USER,
        'delete': Role.USER
    },    
    '/users': {
        'get':  Role.USER,
        'post': Role.USER,
    },
    '/users/+': {
        'get':    Role.USER,
        'put':    Role.USER,
        'delete': Role.USER
    },
    '/user_recipes/+': {
        'get': Role.USER,
    },    
    '/saved_recipes/+': {
        'get': Role.USER,
    },        
    '/user_activity/+': {
        'get': Role.USER,
    },
    '/recipe_liked/+':{
        'post': Role.USER,
    },
    '/recipe_saved/+':{
        'post': Role.USER,
    },
    '/activity_liked/+':{
        'post': Role.USER,
    },
    '/get_userid': {
        'post': Role.USER
    },    
    '/feed': {
        'get':  Role.USER,
    },    
    '/groups': {
        'get':  Role.USER,
        'post': Role.USER,
    },
    '/groups/+': {
        'get':    Role.USER,
        'put':    Role.USER,
        'delete': Role.USER
    },
    '/group_recipes/+': {
        'get':    Role.USER,
    },            
    '/contacts/+': {
        'get':    Role.USER,
        'put':    Role.USER,
        'delete': Role.USER
    },
    '/followers/+': {
        'get':    Role.USER,
        'put':    Role.USER,
        'delete': Role.USER
    },
    '/following/+': {
        'get':    Role.USER,
        'put':    Role.USER,
        'delete': Role.USER
    },    
    '/verify': {
        'get':  Role.USER,
        'post': Role.USER,
    },    
    '/login': {
        'get':  Role.USER,
        'post': Role.USER,
    },
    '/register': {
        'get':  Role.USER,
        'post': Role.USER,
    },     
}

      
@falcon.before(supply_redis_conn)      
@falcon.before(deserialize)
@falcon.after(serialize)
class VerifyPhoneResource(object):

    def __init__(self, get_user, secret, token_expiration_seconds, **token_opts):
        
        self.get_user = get_user
        self.secret = secret
        self.token_expiration_seconds = token_expiration_seconds
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS
        logger.debug(token_opts)
        
    @falcon.after(kafka_verify_producer)
    @statsd.timer('user_verification_post')
    def on_post(self, req, resp):
        # Used to send the OTP for verificiation
        statsd.incr('verification.invocations')
        challenges = ['Hello="World"']
        logger.debug("Reached on_post() in VerifyPhone")
        req.kafka_topic_name = 'verify_phone'
        resp.body = {}
        otp_code = req.params['body']["code"]
        
        logger.debug(req.get_header("auth_token"))
        logger.debug(self.token_opts['location'])
        
        if self.token_opts.get('location', 'cookie') == 'cookie':
            token = req.cookies.get(self.token_opts.get("name"))
        elif self.token_opts['location'] == 'header':
            
            token = req.get_header(self.token_opts.get("name"), required=True)
        else:
            # Unrecognized token location
            token = None

        logger.debug(token)
        if token is None:
            description = ('Please provide an auth token as part of the request.')
            raise falcon.HTTPPreconditionFailed('Auth token required',
                                                description,
                                                href='http://docs.example.com/auth')

        if not self._token_is_valid(resp, token):
            description = ('The provided auth token is not valid. '
                           'Please request a new token and try again.')
            raise falcon.HTTPUnauthorized('Authentication required',
                                          description,
                                          challenges,
                                          href='http://docs.example.com/auth')
        
        phone_number = self.decoded.pop("user_identifier")        
        req.user_id = phone_number
        user_otp = req.redis_conn.get(OTP+phone_number)
        
        if not user_otp:
            description = ('OTP expired, please request new OTP.')
            raise falcon.HTTPForbidden('OTP expired!',
                                       description,
                                       href='http://docs.example.com/auth')                                       
        else:
            logger.debug("Verifying user...")
            if otp_code == user_otp:
                current_time = datetime.utcnow()
                logger.debug("Current time!")
                logger.debug(str(current_time))
                full_user = self.get_user('phone', phone_number)
                full_user.update(**{'phone_verified':True,
                                    'account_active': True,
                                    'phone_last_verified':str(current_time)} # This gives error if we use datetime type instead of str
                                 )
                # Store phone to MongoDB mapping in Redis database
                pipeline = req.redis_conn.pipeline(True)
                pipeline.set(phone_number, str(full_user.id))
                # For redis we can't use bool, so using ints
                pipeline.hmset(USER+str(full_user.id), {'account_active':1,
                                                        'public_profile':0})                
                pipeline.execute()
                
                # Add some public recipes to user feed if the user is new
                user_feed = USER_FEED + str(full_user.id)
                if not req.redis_conn.exists(user_feed):
                    # Get public recipe list along with time stamp
                    recipes_scored_list = req.redis_conn.zrange(PUBLIC_RECIPES, 0, 50, withscores=True)
                    recipes_scored_dict = dict(recipes_scored_list)
                    if len(recipes_scored_dict) > 0:
                        logger.debug("Adding following public recipes to user feed:")
                        logger.debug(recipes_scored_dict)
                        req.redis_conn.zadd(user_feed, recipes_scored_dict)
                    else:    
                        logger.warn("No public recipes available to add user feed!")
                else: 
                    logger.info("User is a returning user!")
                    
                logger.info("User verification: Success")
                self.add_new_jwtoken(resp, str(full_user.id), phone_last_verified=current_time)
                resp.status = falcon.HTTP_ACCEPTED
            else:
                logger.error("Incorrect OTP code!")
                description = ('Incorrect OTP code! Please try again.')
                raise falcon.HTTPNotAcceptable(description,
                                               href='http://docs.example.com/auth')                
                       
    def _token_is_valid(self, resp, token):
        try:
            options = {'verify_exp': True}
            self.decoded = jwt.decode(token, self.secret, verify='True', algorithms=['HS256'], options=options)
            return True
        except jwt.DecodeError as err:
            logger.debug("Token validation failed Error :{}".format(str(err)))
            return False        

    def add_new_jwtoken(self, resp, user_identifier=None, phone_last_verified=None):
        # add a JSON web token to the response headers
        if not user_identifier:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise Exception('Empty user_identifer passed to set JWT')
        logger.debug(
            "Creating new JWT, user_identifier is: {}".format(user_identifier))
        logger.debug(datetime.utcnow() + timedelta(seconds=self.token_expiration_seconds))
        logger.debug(phone_last_verified)
        token = jwt.encode({'user_identifier': user_identifier,
                            'exp': datetime.utcnow() + timedelta(seconds=self.token_expiration_seconds),
                            'phone_last_verified': str(phone_last_verified)},
                            self.secret,
                            algorithm='HS256').decode("utf-8")
        logger.debug("Setting TOKEN!")
        self.token_opts["value"] = token
        logger.debug(self.token_opts)
        
        if self.token_opts.get('location', 'cookie') == 'cookie': # default to cookie
            resp.set_cookie(**self.token_opts)
        elif self.token_opts['location'] == 'header':
            resp.body.update({self.token_opts['name'] : self.token_opts['value'],
                              "user_identifier": user_identifier})
        else:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            raise falcon.HTTPInternalServerError('Unrecognized jwt token location specifier')
        resp.status = falcon.HTTP_ACCEPTED #HTTP_202
        
@falcon.before(supply_redis_conn)        
@falcon.before(deserialize)
@falcon.after(serialize)
class RegisterResource(object):

    def __init__(self, get_user, secret, verify_phone_token_expiration_seconds, **token_opts):
        self.get_user = get_user
        self.secret = secret
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS
        self.verify_phone_token_expiration_seconds = verify_phone_token_expiration_seconds        
       
    @falcon.after(kafka_register_producer)
    @statsd.timer('user_registration_post')
    def on_post(self, req, resp):
        # Should we check if the number supplied is same as the number verified?
        # Can we do this in client instead of server?
        statsd.incr('registration.invocations')
        logger.debug("Reached on_post() in Register")
        req.kafka_topic_name = 'register'
        resp.body = {}
      
        phone = req.params['body']["phone"]
        user = self.get_user('phone', phone)
        
        logger.debug("getting user")
        logger.debug(user)
        if not user:
            logger.debug("Adding new user...")
            # We don't check of display name is unique. We only check for email and phone 
            new_user = User(phone=phone, 
                            country_code=req.params['body']["country_code"])
            new_user.save()
        
            if 'public_profile' in req.params['body']:
                new_user.update(public_profile=req.params['body']['public_profile'])
            logger.debug("Added new user. Please verify phone number")
            
        logger.debug("Sending SMS to user ...")
        if SERVER_RUN_MODE == 'DEBUG':
            logger.warn("SERVER RUNNING in DEBUG Mode")
            otpass = repr(999999)
            response = [202]
        else:    
            # Plivo does not accept 0044, only accepts +44
            otpass = random_with_N_digits(OTP_LENGTH)
            plivo_valid_dst = '+' + phone[2:]
            params = {
                'src': SRC_PHONE_NUM, # Sender's phone number with country code
                'dst' : plivo_valid_dst,  # Receiver's phone Number with country code
                'text' : u"Your UggiPuggi OTP: %s" %otpass, # Your SMS Text Message - English
            }
            
            response = sms.send_message(params)
            logger.debug(response)                
            
        logger.debug(otpass)
        if response[0] == 202:
            # See if there is a user with that phone in verify_user DB
            req.redis_conn.set(OTP+phone, otpass)
            req.redis_conn.expire(OTP+phone, self.verify_phone_token_expiration_seconds)
            logger.debug("Added new user in verify database as sms OTP successful")
            self.add_new_jwtoken(resp, phone)
            resp.status = falcon.HTTP_OK
        else:
            logger.debug("OTP SMS failed!")
            raise falcon.HTTPBadRequest(
                            "OTP SMS failed!", traceback.format_exc())

    # given a user identifier, this will add a new token to the response
    # Typically you would call this from within your login function, after the
    # back end has OK'd the username/password
    def add_new_jwtoken(self, resp, user_identifier=None):
        # add a JSON web token to the response headers
        if not user_identifier:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise Exception('Empty user_identifer passed to set JWT')
        logger.debug(
            "Creating new JWT, user_identifier is: {}".format(user_identifier))
        token = jwt.encode({'user_identifier': user_identifier,
                            'exp': datetime.utcnow() + timedelta(seconds=self.verify_phone_token_expiration_seconds)},
                            self.secret,
                            algorithm='HS256').decode("utf-8")
        logger.debug("Setting TOKEN!")
        self.token_opts["value"] = token
        logger.debug(self.token_opts)
        if self.token_opts.get('location', 'cookie') == 'cookie': # default to cookie
            resp.set_cookie(**self.token_opts)
        elif self.token_opts['location'] == 'header':
            resp.body.update({self.token_opts['name'] : self.token_opts['value']})
            #resp.body = json_util.dumps(resp.body)
        else:
            raise falcon.HTTPInternalServerError('Unrecognized jwt token location specifier')
        resp.status = falcon.HTTP_CREATED #HTTP_201


@falcon.before(deserialize)
@falcon.after(serialize)
class LoginResource(object):

    def __init__(self, get_user, secret, token_expiration_seconds, **token_opts):
        self.get_user = get_user
        self.secret = secret
        self.token_expiration_seconds = token_expiration_seconds
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS
        logger.debug(token_opts)

    @falcon.after(kafka_login_producer)
    @statsd.timer('user_login_post')
    def on_post(self, req, resp):
        statsd.incr('login.invocations')
        logger.debug("Reached on_post() in Login")
        req.kafka_topic_name = 'login'
        resp.body = {}

        email = req.params['body']["email"]
        password = req.params['body']["password"]
        logger.debug("getting user")
        user = self.get_user('email', email)
        if user:
            logger.debug(user.id)
            if not user.phone_verified:
                raise falcon.HTTPUnauthorized('Phone not verified. Please verify phone.',
                                              'User did not verify phone.',
                                              ['Hello="World!"'])                
            if crypt.verify(password, user["password"]):
                logger.debug("Valid user, jwt'ing!")
                self.add_new_jwtoken(resp, str(user.id), user.pw_last_changed)
                resp.status = falcon.HTTP_ACCEPTED #HTTP_202
            else:
                description = ('Password did not match, please try again')
                raise falcon.HTTPForbidden('Login Failed',
                                           description
                                          )
        else:
            raise falcon.HTTPUnauthorized('Login Failed',
                                          'User with this email does not exist, please try again',
                                          ['Hello="World!"'])
            

    # given a user identifier, this will add a new token to the response
    # Typically you would call this from within your login function, after the
    # back end has OK'd the username/password
    def add_new_jwtoken(self, resp, user_identifier=None, pw_last_changed=None):
        # add a JSON web token to the response headers
        if not user_identifier:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise Exception('Empty user_identifer passed to set JWT')
        logger.debug(
            "Creating new JWT, user_identifier is: {}".format(user_identifier))
        logger.debug(datetime.utcnow() + timedelta(seconds=self.token_expiration_seconds))
        logger.debug(pw_last_changed + timedelta(seconds=self.token_expiration_seconds))
        token = jwt.encode({'user_identifier': user_identifier,
                            'exp': datetime.utcnow() + timedelta(seconds=self.token_expiration_seconds),
                            'pw_last_changed': str(pw_last_changed)},
                            self.secret,
                            algorithm='HS256').decode("utf-8")
        logger.debug("Setting TOKEN!")
        self.token_opts["value"] = token
        logger.debug(self.token_opts)
        
        if self.token_opts.get('location', 'cookie') == 'cookie': # default to cookie
            resp.set_cookie(**self.token_opts)
        elif self.token_opts['location'] == 'header':
            resp.body.update({self.token_opts['name'] : self.token_opts['value'],
                              "user_identifier": user_identifier})
        else:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            raise falcon.HTTPInternalServerError('Unrecognized jwt token location specifier')
        resp.status = falcon.HTTP_ACCEPTED #HTTP_202

class LogoutResource(object):

    def __init__(self, get_user):
        self.get_user = get_user
        self.kafka_topic_name = 'logout'

    @falcon.after(kafka_logout_producer)
    @statsd.timer('user_logout_post')
    def on_post(self, req, resp):
        statsd.incr('logout.invocations')
        logger.debug("Reached on_post() in Logout")
        req.kafka_topic_name = 'logout'
        
        user = self.get_user('id', req.user_id)
        if user:
            logger.debug(user.id)
            if not user.phone_verified:
                raise falcon.HTTPUnauthorized('Phone not verified. Please verify phone.',
                                              'User did not verify phone.',
                                              ['Hello="World!"']) 
            user.update(phone_last_verified=datetime.utcnow())
            resp.status = falcon.HTTP_OK
        else:
            raise falcon.HTTPUnauthorized('Logout Failed',
                                          'User with this phone number does not exist, please register',
                                          ['Hello="World!"'])

            
@falcon.before(deserialize)
@falcon.after(serialize)
class ForgotPasswordResource(object):

    def __init__(self, get_user):
        self.get_user = get_user

    @falcon.after(kafka_forgotpassword_producer)
    @statsd.timer('user_forgot_password_post')
    def on_post(self, req, resp):
        # Should we check if the number supplied is same as the number verified?
        # Can we do this in client instead of server?
        statsd.incr('forgot_password.invocations')
        logger.debug("Reached on_post() in ForgotPassword")
        req.kafka_topic_name = 'forgotpassword'

        email = req.params['body']["email"]
        user = self.get_user('email', email)
        
        logger.debug("getting user")
        logger.debug(user)
        if user:
            random_password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(5))
            user.update(password=crypt.encrypt(random_password))
            user.update(pw_last_changed=datetime.utcnow())
            requests.post(
                os.environ["MAILGUN_SERVER"],
                auth=("api", os.environ["MAILGUN_APIKEY"]),
                data={"from": "UggiPuggi Temporary Password <uggi.puggi@gmail.com>",
                      "to": [email],
                      "subject": "UggiPuggi Temporary Password",
                      "text": "Your UggiPuggi temporary password: %s \n Please change it immediately after login. \n Automatically generated, do not reply to this email."%random_password,
                      "html": "<html>Your UggiPuggi temporary password: <b>%s</b> \n Please change it immediately after login. \n Automatically generated, do not reply to this email.</html>"%random_password})
            resp.status = falcon.HTTP_ACCEPTED #HTTP_202
        else:
            raise falcon.HTTPUnauthorized('User with this email does not exists!',
                                          'Please register.',
                                          ['Hello="World!"'])


@falcon.before(deserialize)
@falcon.after(serialize)
class PasswordChangeResource(object):

    def __init__(self, get_user, secret, token_expiration_seconds, **token_opts):
        self.get_user = get_user
        self.secret = secret
        self.token_expiration_seconds = token_expiration_seconds
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS
        logger.debug(token_opts)
        
    @falcon.after(kafka_passwordchange_producer)
    @statsd.timer('user_password_change_post')
    def on_post(self, req, resp):
        statsd.incr('password_change.invocations')
        logger.debug("Reached on_post() in PasswordChange")
        req.kafka_topic_name = 'passwordchange'
        
        logger.debug(req.params['body'])
        email = req.params['body']["email"]
        password = req.params['body']["password"]
        new_password = req.params['body']["new_password"]
        logger.debug("getting user")
        user = self.get_user('email', email)
        if user:
            logger.debug(user.id)
            if crypt.verify(password, user["password"]):
                logger.debug("Valid user, jwt'ing!")
                user.update(password=crypt.encrypt(new_password))
                user.update(pw_last_changed=datetime.utcnow())                
                # We need to give new token when password changes.
                # All previously given tokens are now invalid
                self.add_new_jwtoken(resp, user.email, user.pw_last_changed)
                resp.status = falcon.HTTP_ACCEPTED #HTTP_202
            else:
                description = ('Old password did not match')
                raise falcon.HTTPForbidden('Password change Failed',
                                           description)
        else:
            raise falcon.HTTPUnauthorized('Login Failed',
                                          'User with this email does not exist, please try again',
                                          ['Hello="World!"'])
        logger.debug("Password change successful")    

    # given a user identifier, this will add a new token to the response
    # Typically you would call this from within your login function, after the
    # back end has OK'd the username/password
    def add_new_jwtoken(self, resp, user_identifier=None, pw_last_changed=None):
        # add a JSON web token to the response headers
        if not user_identifier:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise Exception('Empty user_identifer passed to set JWT')
        logger.debug(
            "Creating new JWT, user_identifier is: {}".format(user_identifier))
        logger.debug(datetime.utcnow() + timedelta(seconds=self.token_expiration_seconds))
        logger.debug(pw_last_changed + timedelta(seconds=self.token_expiration_seconds))
        token = jwt.encode({'user_identifier': user_identifier,
                            'exp': datetime.utcnow() + timedelta(seconds=self.token_expiration_seconds),
                            'pw_last_changed': str(pw_last_changed)},
                            self.secret,
                            algorithm='HS256').decode("utf-8")
        logger.debug("Setting TOKEN!")
        self.token_opts["value"] = token
        logger.debug(self.token_opts)
        
        if self.token_opts.get('location', 'cookie') == 'cookie': # default to cookie
            resp.set_cookie(**self.token_opts)
        elif self.token_opts['location'] == 'header':
            resp.body = {self.token_opts['name'] : self.token_opts['value'],
                         "user_identifier": user_identifier
                        }
        else:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            raise falcon.HTTPInternalServerError('Unrecognized jwt token location specifier')
        resp.status = falcon.HTTP_ACCEPTED #HTTP_202

        
class AuthMiddleware(object):

    def __init__(self, get_user, secret, **token_opts):
        self.secret = secret
        self.get_user = get_user
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS

    def process_resource(self, req, resp, resource, params): # pylint: disable=unused-argument
        logger.debug("Req URL: " + req.url)
        logger.debug("Req method: " + req.method.lower())
        if isinstance(resource, RegisterResource) or \
           isinstance(resource, VerifyPhoneResource) or \
           isinstance(resource, PasswordChangeResource) or \
           isinstance(resource, ForgotPasswordResource) or \
           isinstance(resource, PrometheusMiddleware) or \
           isinstance(resource, Ping) or ("/images/" in req.url and req.method.lower()=='get'):
            logger.debug("DON'T NEED TOKEN")
            return
        
        challenges = ['Hello="World"']  # I think this is very irrelevant
            
        if self.token_opts.get('location', 'cookie') == 'cookie':
            token = req.cookies.get(self.token_opts.get("name"))
        elif self.token_opts['location'] == 'header':
            token = req.get_header(self.token_opts.get("name"), required=True)
        else:
            # Unrecognized token location
            token = None

        logger.debug("Got hold of the token from request")
        if token is None:
            logger.error("Please provide an auth token as part of the request.")
            description = ('Please provide an auth token as part of the request.')
            raise falcon.HTTPPreconditionFailed('Auth token required',
                                                description,
                                                href='http://docs.example.com/auth')
        
        if not self._token_is_valid(resp, token):
            logger.debug(token)
            logger.error('The provided auth token is not valid. Please request a new token and try again.')
            description = ('The provided auth token is not valid. '
                           'Please request a new token and try again.')
            resp.status = falcon.HTTP_UNAUTHORIZED
            raise falcon.HTTPUnauthorized('Authentication required',
                                          description,
                                          challenges,
                                          href='http://docs.example.com/auth')
        
        logger.debug("Token looks fine")
        # we used user mongo object id as user identifier
        user_id = self.decoded.pop("user_identifier")
        req.user_id = user_id
        logger.debug("User id decoded from auth_token: %s" %repr(user_id))
        phone_last_verified = self.decoded.pop("phone_last_verified")
        logger.debug("Password last changed recovered from auth_token:")
        logger.debug(phone_last_verified)
        # check if user is authorized to this request
        if not self._is_user_authorized(req, user_id, phone_last_verified, user_id_type='id'):
            resp.status = falcon.HTTP_UNAUTHORIZED
            logger.error("Authorization Failed: User does not have privilege/permission or supplied expired token.")
            raise falcon.HTTPUnauthorized(
                title='Authorization Failed',
                description='User does not have privilege/permission to view requested resource.'
            )

    def _token_is_valid(self, resp, token):
        try:
            options = {'verify_exp': True}
            self.decoded = jwt.decode(token, self.secret, verify='True', algorithms=['HS256'], options=options)
            resp.status = falcon.HTTP_ACCEPTED
            return True
        except jwt.DecodeError as err:
            resp.status = falcon.HTTP_UNAUTHORIZED
            logger.error("Token validation failed Error :{}".format(str(err)))
            return False

    def _access_allowed(self, req, user):
        logger.debug("Checking if user is allowed access or not ...")
        method = req.method.lower() or 'get'
        path = req.path.lower()
        logger.debug("method: %s" %repr(method))
        logger.debug("path: %s" %repr(path))
        
        if path not in ACL_MAP:
            # try replacing :id value with `+`
            sub_path, _, id = path.rpartition('/')
            if not sub_path:
                return False  # unable to find a logical path for ACL checking
            path = "{}/+".format(sub_path)
            if path not in ACL_MAP:
                return False
            
        logger.debug("Required role: %s" %repr(ACL_MAP[path].get(method, Role.USER)))
        return user.role_satisfy(ACL_MAP[path].get(method, Role.USER))  # defaults to minimal role if method not found

    def _is_user_authorized(self, req, user_id, phone_last_verified, user_id_type='phone'):
        user = self.get_user(user_id_type, user_id)
        if user.phone_last_verified != phone_last_verified:
            logger.error(user.phone_last_verified)
            logger.error(phone_last_verified)
            logger.error("Supplied authentication token is expired. Please supply new token.")
            return False
        return user is not None and self._access_allowed(req, user)

def get_auth_objects(get_user, secret, token_expiration_seconds, verify_phone_token_expiration_seconds, token_opts=DEFAULT_TOKEN_OPTS): # pylint: disable=dangerous-default-value
    return ForgotPasswordResource(get_user),\
           RegisterResource(get_user, secret, verify_phone_token_expiration_seconds, **token_opts),\
           LogoutResource(get_user),\
           PasswordChangeResource(get_user, secret, token_expiration_seconds, **token_opts),\
           VerifyPhoneResource(get_user, secret, token_expiration_seconds, **token_opts),\
           AuthMiddleware(get_user, secret, **token_opts)
