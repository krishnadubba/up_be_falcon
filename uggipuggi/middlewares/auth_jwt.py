from datetime import datetime, timedelta
import traceback
#import json
from bson import json_util
import logging

import falcon
import jwt
from passlib.hash import bcrypt as crypt

from uggipuggi.models.user import Role, User


DEFAULT_TOKEN_OPTS = {"name": "auth_token", "location":"cookie"}

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
}

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
            if isinstance(req_stream, bytes):
                data = json_util.loads(req_stream.decode('utf8'))
            else:
                data = json_util.loads(req_stream)
        except Exception:
            raise falcon.HTTPBadRequest(
                "I don't understand", traceback.format_exc())
        email = data["email"]
        password = data["password"]
        user = self.get_user(email)
        if user:
            if crypt.verify(password, user["password"]):
                logging.debug("Valid user, jwt'ing!")
                self.add_new_jwtoken(resp, email)
            else:
                raise falcon.HTTPUnauthorized('Login Failed',
                                              'Bad email/phone number/password combination, please try again',
                                              ['Hello="World!"'])
        else:
            new_user = User(email=email, password=crypt.encrypt(password), tel=data["tel"], 
                            country_code=data["country_code"], display_name=data["display_name"])
            new_user.save()
    
            res.body = new_user
            

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
        if self.token_opts.get('location', 'cookie') == 'cookie': # default to cookie
            resp.set_cookie(**self.token_opts)
        elif self.token_opts['location'] == 'header':
            resp.body = json.dumps({
                self.token_opts['name'] : self.token_opts['value']
                })
        else:
            raise falcon.HTTPInternalServerError('Unrecognized jwt token location specifier')


class AuthMiddleware(object):

    def __init__(self, get_user, secret, **token_opts):
        self.secret = secret
        self.get_user = get_user
        self.token_opts = token_opts or DEFAULT_TOKEN_OPTS

    def process_resource(self, req, resp, resource, params): # pylint: disable=unused-argument
        logging.debug("Processing request in AuthMiddleware: ")
        if isinstance(resource, LoginResource):
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

            raise falcon.HTTPUnauthorized('Auth token required',
                                          description,
                                          challenges,
                                          href='http://docs.example.com/auth')

        if not self._token_is_valid(token):
            description = ('The provided auth token is not valid. '
                           'Please request a new token and try again.')

            raise falcon.HTTPUnauthorized('Authentication required',
                                          description,
                                          challenges,
                                          href='http://docs.example.com/auth')
        
        user_id = self.decoded.pop("sub")
        self.decoded.pop("acl")

        # check if user is authorized to this request
        if not self._is_user_authorized(req, user_id):
            raise HTTPUnauthorized(
                title='Authorization Failed',
                description='User does not have privilege/permission to view requested resource.'
            )        

    def _token_is_valid(self, token):
        try:
            options = {'verify_exp': True}
            self.decoded = jwt.decode(token, self.secret, verify='True', algorithms=['HS256'], options=options)
            return True
        except jwt.DecodeError as err:
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
        user = self.get_user(user_id)
        return user is not None and self._access_allowed(req, user)

def get_auth_objects(get_user, secret, token_expiration_seconds, token_opts=DEFAULT_TOKEN_OPTS): # pylint: disable=dangerous-default-value
    return LoginResource(get_user, secret, token_expiration_seconds, **token_opts), AuthMiddleware(get_user, secret, **token_opts)
