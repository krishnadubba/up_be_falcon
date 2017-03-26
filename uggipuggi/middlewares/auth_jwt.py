import traceback
import logging
import falcon
import jwt
import os
import plivo

from random import randint
from bson import json_util
from datetime import datetime, timedelta
from passlib.hash import bcrypt as crypt
from uggipuggi.models.user import Role, User, VerifyPhone

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return repr(randint(range_start, range_end))

DEFAULT_TOKEN_OPTS = {"name": "auth_token", "location": "header"}

# role-based permission control
ACL_MAP = {
    '/recipes': {
        'get': Role.USER,
        'post': Role.OWNER
    },
    '/recipes/+': {
        'get': Role.USER,
        'put': Role.OWNER,
        'delete': Role.OWNER
    },
    
    '/users': {
        'get': Role.EMPLOYEE,
        'post': Role.EMPLOYEE,
    },
    '/users/+': {
        'get': Role.USER,
        'put': Role.EMPLOYEE,
        'delete': Role.EMPLOYEE
    },
    '/verify': {
        'get': Role.USER,
        'post': Role.USER,
    },    
    '/login': {
        'get': Role.USER,
        'post': Role.USER,
    },
    '/register': {
        'get': Role.USER,
        'post': Role.USER,
    },     
}

class VerifyPhoneResource(object):

    def __init__(self, get_user, secret, verify_phone_token_expiration_seconds, **token_opts):
        sms_auth_id = os.environ["SMS_AUTH_ID"]
        sms_auth_token = os.environ["SMS_AUTH_TOKEN"]
        
        self.sms = plivo.RestAPI(sms_auth_id, sms_auth_token)
        
        self.get_user = get_user
        self.secret = secret
        self.verify_phone_token_expiration_seconds = verify_phone_token_expiration_seconds
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS
        logging.debug(token_opts)

    def on_post(self, req, resp):
        logging.debug("Reached on_post() in VerifyPhone")
        try:
            req_stream = req.stream.read()
            logging.debug("req_stream")
            logging.debug(req_stream)
            
            if isinstance(req_stream, bytes):
                data = json_util.loads(req_stream.decode('utf8'))
            else:
                data = json_util.loads(req_stream)
        except Exception:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise falcon.HTTPBadRequest(
                "I don't understand", traceback.format_exc())
        
        logging.debug(data)
        phone_number = data["phone"]
        user = self.get_user('phone', phone_number, verify=True)
        if user:
            logging.debug("getting user")
            logging.debug(user.phone)            
            resp.status = falcon.HTTP_UNAUTHORIZED
            raise falcon.HTTPUnauthorized('User already exists with this phone number!',
                                          'Please login.',
                                          ['Hello="World!"'])
        else:
            logging.debug("Sending SMS to new user ...")
            otpass = random_with_N_digits(4)
            
            params = {
                'src': '0044790110313', # Sender's phone number with country code
                'dst' : phone_number,  # Receiver's phone Number with country code
                'text' : u"Your UggiPuggi OTP: %s" %otpass, # Your SMS Text Message - English
                #'url' : "http://example.com/report/", # The URL to which with the status of the message is sent
                'method' : 'POST' # The method used to call the url
            }
            
            response = self.sms.send_message(params)
            logging.debug(response)
            if response[0] == 202:                
                new_user = VerifyPhone(phone=data["phone"], otp=otpass)
                new_user.save()
                logging.debug("Added new user in verify database as sms OTP successful")
                self.add_new_jwtoken(resp, phone_number)
                resp.status = falcon.HTTP_OK
            else: 
                raise falcon.HTTPBadRequest(
                                "OTP SMS failed!", traceback.format_exc())
            
    def on_get(self, req, resp):
        challenges = ['Hello="World"']
        logging.debug("Reached on_get() in VerifyPhone")
        try:
            req_stream = req.stream.read()
            logging.debug("req_stream")
            logging.debug(req_stream)
            
            if isinstance(req_stream, bytes):
                data = json_util.loads(req_stream.decode('utf8'))
            else:
                data = json_util.loads(req_stream)
        except Exception:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise falcon.HTTPBadRequest(
                "I don't understand", traceback.format_exc())
        
        logging.debug(data)
        otp_code = data["code"]
        
        logging.debug(req.get_header("auth_token"))
        logging.debug(self.token_opts['location'])
        
        if self.token_opts.get('location', 'cookie') == 'cookie':
            token = req.cookies.get(self.token_opts.get("name"))
        elif self.token_opts['location'] == 'header':
            
            token = req.get_header(self.token_opts.get("name"), required=True)
        else:
            # Unrecognized token location
            token = None

        if token is None:
            description = ('Please provide an auth token '
                           'as part of the request.')
            resp.status = falcon.HTTP_UNAUTHORIZED
            raise falcon.HTTPUnauthorized('Auth token required',
                                          description,
                                          challenges,
                                          href='http://docs.example.com/auth')

        if not self._token_is_valid(resp, token):
            description = ('The provided auth token is not valid. '
                           'Please request a new token and try again.')
            resp.status = falcon.HTTP_UNAUTHORIZED
            raise falcon.HTTPUnauthorized('Authentication required',
                                          description,
                                          challenges,
                                          href='http://docs.example.com/auth')
        
        phone_number = self.decoded.pop("user_identifier")        

        # Use VerifyUser database instead of normal User database
        user = self.get_user('phone', phone_number, verify=True)
        logging.debug("getting user from VerifyUser database")
        logging.debug(user)        
        if not user:
            resp.status = falcon.HTTP_UNAUTHORIZED
            raise falcon.HTTPUnauthorized('User record with this phone number does not exists!',
                                          'Please try again.',
                                          ['Hello="World!"'])
        else:
            logging.debug("Verifying user...")
            if otp_code == user.otp:
                logging.debug("User verification: Success")
                resp.status = falcon.HTTP_ACCEPTED
            else:
                logging.debug("'Incorrect OTP code!")
                raise falcon.HTTPUnauthorized('Incorrect OTP code!',
                                              'Please try again.',
                                              ['Hello="World!"'])
                

    # given a user identifier, this will add a new token to the response
    # Typically you would call this from within your login function, after the
    # back end has OK'd the username/password
    def add_new_jwtoken(self, resp, user_identifier=None):
        # add a JSON web token to the response headers
        if not user_identifier:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise Exception('Empty user_identifer passed to set JWT')
        logging.debug(
            "Creating new JWT, user_identifier is: {}".format(user_identifier))
        token = jwt.encode({'user_identifier': user_identifier,
                            'exp': datetime.utcnow() + timedelta(seconds=self.verify_phone_token_expiration_seconds)},
                           self.secret,
                           algorithm='HS256').decode("utf-8")
        logging.debug("Setting TOKEN!")
        self.token_opts["value"] = token
        logging.debug(self.token_opts)
        if self.token_opts.get('location', 'cookie') == 'cookie': # default to cookie
            resp.set_cookie(**self.token_opts)
        elif self.token_opts['location'] == 'header':
            resp.body = json_util.dumps({
                self.token_opts['name'] : self.token_opts['value']
                })
        else:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR #HTTP_500
            raise falcon.HTTPInternalServerError('Unrecognized jwt token location specifier')
        resp.status = falcon.HTTP_CREATED #HTTP_201
        
    def _token_is_valid(self, resp, token):
        try:
            options = {'verify_exp': True}
            self.decoded = jwt.decode(token, self.secret, verify='True', algorithms=['HS256'], options=options)
            resp.status = falcon.HTTP_ACCEPTED
            return True
        except jwt.DecodeError as err:
            resp.status = falcon.HTTP_UNAUTHORIZED
            logging.debug("Token validation failed Error :{}".format(str(err)))
            return False        
        
class RegisterResource(object):

    def __init__(self, get_user, secret, token_expiration_seconds, **token_opts):
        self.get_user = get_user
        self.secret = secret
        self.token_expiration_seconds = token_expiration_seconds
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS
        logging.debug(token_opts)

    def on_post(self, req, resp):
        logging.debug("Reached on_post() in Register")
        try:
            req_stream = req.stream.read()
            logging.debug("req_stream")
            logging.debug(req_stream)
            
            if isinstance(req_stream, bytes):
                data = json_util.loads(req_stream.decode('utf8'))
            else:
                data = json_util.loads(req_stream)
        except Exception:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise falcon.HTTPBadRequest(
                "I don't understand", traceback.format_exc())
        
        logging.debug(data)
        email = data["email"]
        password = data["password"]
        user = self.get_user('email', email)
        logging.debug("getting user")
        logging.debug(user)
        if user:
            resp.status = falcon.HTTP_UNAUTHORIZED
            raise falcon.HTTPUnauthorized('User already exists!',
                                          'Please login.',
                                          ['Hello="World!"'])
        else:
            logging.debug("Adding new user...")
            new_user = User(email=email, password=crypt.encrypt(password), tel=data["tel"], 
                            country_code=data["country_code"], display_name=data["display_name"])
            new_user.save()
            logging.debug("Added new user")
            self.add_new_jwtoken(resp, email)

    # given a user identifier, this will add a new token to the response
    # Typically you would call this from within your login function, after the
    # back end has OK'd the username/password
    def add_new_jwtoken(self, resp, user_identifier=None):
        # add a JSON web token to the response headers
        if not user_identifier:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise Exception('Empty user_identifer passed to set JWT')
        logging.debug(
            "Creating new JWT, user_identifier is: {}".format(user_identifier))
        token = jwt.encode({'user_identifier': user_identifier,
                            'exp': datetime.utcnow() + timedelta(seconds=self.token_expiration_seconds)},
                           self.secret,
                           algorithm='HS256').decode("utf-8")
        logging.debug("Setting TOKEN!")
        self.token_opts["value"] = token
        logging.debug(self.token_opts)
        if self.token_opts.get('location', 'cookie') == 'cookie': # default to cookie
            resp.set_cookie(**self.token_opts)
        elif self.token_opts['location'] == 'header':
            resp.body = json_util.dumps({
                self.token_opts['name'] : self.token_opts['value']
                })
        else:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR #HTTP_500
            raise falcon.HTTPInternalServerError('Unrecognized jwt token location specifier')
        resp.status = falcon.HTTP_CREATED #HTTP_201

class LoginResource(object):

    def __init__(self, get_user, secret, token_expiration_seconds, **token_opts):
        self.get_user = get_user
        self.secret = secret
        self.token_expiration_seconds = token_expiration_seconds
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS
        logging.debug(token_opts)

    def on_post(self, req, resp):
        logging.debug("Reached on_post() in Login")
        try:
            req_stream = req.stream.read()
            logging.debug("req_stream")
            logging.debug(req_stream)
            
            if isinstance(req_stream, bytes):
                data = json_util.loads(req_stream.decode('utf8'))
            else:
                data = json_util.loads(req_stream)
        except Exception:
            resp.status = falcon.HTTP_BAD_REQUEST
            raise falcon.HTTPBadRequest(
                "I don't understand", traceback.format_exc())
        
        logging.debug(data)
        email = data["email"]
        password = data["password"]
        user = self.get_user('email', email)
        logging.debug("getting user")
        logging.debug(user)
        if user:
            if crypt.verify(password, user["password"]):
                logging.debug("Valid user, jwt'ing!")
                self.add_new_jwtoken(resp, email)
                resp.status = falcon.HTTP_ACCEPTED #HTTP_202
            else:
                resp.status = falcon.HTTP_FORBIDDEN #HTTP_401
                raise falcon.HTTPUnauthorized('Login Failed',
                                              'Password did not match, please try again',
                                              ['Hello="World!"'])
        else:
            resp.status = falcon.HTTP_UNAUTHORIZED #HTTP_401
            raise falcon.HTTPUnauthorized('Login Failed',
                                          'User with this email does not exist, please try again',
                                          ['Hello="World!"'])
            

    # given a user identifier, this will add a new token to the response
    # Typically you would call this from within your login function, after the
    # back end has OK'd the username/password
    def add_new_jwtoken(self, resp, user_identifier=None):
        # add a JSON web token to the response headers
        if not user_identifier:
            raise Exception('Empty user_identifer passed to set JWT')
        logging.debug(
            "Creating new JWT, user_identifier is: {}".format(user_identifier))
        token = jwt.encode({'user_identifier': user_identifier,
                            'exp': datetime.utcnow() + timedelta(seconds=self.token_expiration_seconds)},
                           self.secret,
                           algorithm='HS256').decode("utf-8")
        logging.debug("Setting TOKEN!")
        self.token_opts["value"] = token
        logging.debug(self.token_opts)
        options = {'verify_exp': True}
        self.decoded = jwt.decode(token, self.secret, verify='True', algorithms=['HS256'], options=options)        
        logging.debug(self.decoded)
        user_id = self.decoded.pop("user_identifier")
        logging.debug(user_id)
        if self.token_opts.get('location', 'cookie') == 'cookie': # default to cookie
            resp.set_cookie(**self.token_opts)
        elif self.token_opts['location'] == 'header':
            resp.body = json_util.dumps({
                self.token_opts['name'] : self.token_opts['value']
                })
        else:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            raise falcon.HTTPInternalServerError('Unrecognized jwt token location specifier')


class AuthMiddleware(object):

    def __init__(self, get_user, secret, **token_opts):
        self.secret = secret
        self.get_user = get_user
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS

    def process_resource(self, req, resp, resource, params): # pylint: disable=unused-argument
        logging.debug("Processing request in AuthMiddleware: ")
        if isinstance(resource, LoginResource) or isinstance(resource, RegisterResource) or isinstance(resource, VerifyPhoneResource):
            logging.debug("LOGIN, DON'T NEED TOKEN")
            return
        
        challenges = ['Hello="World"']  # I think this is very irrelevant

        if self.token_opts.get('location', 'cookie') == 'cookie':
            token = req.cookies.get(self.token_opts.get("name"))
        elif self.token_opts['location'] == 'header':
            token = req.get_header(self.token_opts.get("name"), required=True)
        else:
            # Unrecognized token location
            token = None

        if token is None:
            description = ('Please provide an auth token '
                           'as part of the request.')
            resp.status = falcon.HTTP_UNAUTHORIZED
            raise falcon.HTTPUnauthorized('Auth token required',
                                          description,
                                          challenges,
                                          href='http://docs.example.com/auth')

        if not self._token_is_valid(resp, token):
            description = ('The provided auth token is not valid. '
                           'Please request a new token and try again.')
            resp.status = falcon.HTTP_UNAUTHORIZED
            raise falcon.HTTPUnauthorized('Authentication required',
                                          description,
                                          challenges,
                                          href='http://docs.example.com/auth')
        
        user_id = self.decoded.pop("user_identifier")
        
        # check if user is authorized to this request
        if not self._is_user_authorized(req, user_id):
            resp.status = falcon.HTTP_UNAUTHORIZED
            raise HTTPUnauthorized(
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
            logging.debug("Token validation failed Error :{}".format(str(err)))
            return False

    def _access_allowed(self, req, user):
        method = req.method.lower() or 'get'
        path = req.path.lower()

        if path not in ACL_MAP:
            # try replacing :id value with `+`
            sub_path, _, id = path.rpartition('/')
            if not sub_path:
                return False  # unable to find a logical path for ACL checking
            path = "{}/+".format(sub_path)
            if path not in ACL_MAP:
                return False

        return user.role_satisfy(ACL_MAP[path].get(method, Role.USER))  # defaults to minimal role if method not found

    def _is_user_authorized(self, req, user_id):
        user = self.get_user('email', user_id)
        return user is not None and self._access_allowed(req, user)

def get_auth_objects(get_user, secret, token_expiration_seconds, verify_phone_token_expiration_seconds, token_opts=DEFAULT_TOKEN_OPTS): # pylint: disable=dangerous-default-value
    return VerifyPhoneResource(get_user, secret, verify_phone_token_expiration_seconds, **token_opts),\
           RegisterResource(get_user, secret, token_expiration_seconds, **token_opts),\
           LoginResource(get_user, secret, token_expiration_seconds, **token_opts),\
           AuthMiddleware(get_user, secret, **token_opts)
