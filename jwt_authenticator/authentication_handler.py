""" JWT authentication handler for Flask web services"""
import os
from functools import wraps
from flask import g, request, current_app as app
from jose import jwt


class AuthError(Exception):
    """ Simple exception object"""
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code
        Exception.__init__(self)


class AuthenticationHandler:
    """ Basic JWT authentication handler """

    @staticmethod
    def load_configuration():
        """ Load configuration from environment variables if set. The application configuration
        values: SECRET and AUDIENCE are expected for this module to work properly.
        Environment variables will override what has already been set in the application config
        (e.g. in config.py) if something has been set. This is helpful when running flask services
        in container environments.
        This method should be called during your application's construction.
         """

        env_secret = os.getenv('JWT_SECRET')
        env_audience = os.getenv('JWT_AUDIENCE')

        if env_secret:
            app.config['SECRET'] = env_secret

        if env_audience:
            app.config['AUDIENCE'] = env_audience

    @staticmethod
    def generate_auth_token(role_claims, key, algorithm='HS256'):
        """Generate a JWT token (mostly for testing)"""

        token = jwt.encode(role_claims, key, algorithm)
        return token

    @staticmethod
    def validate_and_decode_token(token, key, audience, role_name=None, algorithms=None):
        """ Valid the token and decode the payload """

        if not algorithms:
            algorithms = ["HS256"]
        try:
            claim_set = jwt.decode(
                token,
                key,
                audience=audience,
                algorithms=algorithms)

            roles = claim_set["role"]
            if role_name:
                matching_roles = list(filter(lambda x: x.lower() == role_name.lower(), roles))
                if not matching_roles:
                    raise AuthError({"code": "unauthorized",
                                     "description": "not authorized"}, 401)
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                             "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                             "description":
                                 "incorrect claims,"
                                 "please check the audience and issuer"}, 401)
        except AuthError:
            raise

        except Exception:
            raise AuthError({"code": "unknown error",
                             "description":
                                 "Unable to parse authentication"
                                 " token."}, 401)
        return claim_set

    @staticmethod
    def requires_auth(role_name=None):
        """ Validate access token """

        def auth_decorator(func):
            @wraps(func)
            def func_wrapper(*args, **kwargs):
                token = request.headers.get("Authorization", None)
                claim_set = \
                    AuthenticationHandler.validate_and_decode_token(
                        token,
                        app.config['SECRET'],
                        app.config['AUDIENCE'],
                        role_name)
                # if we want to store claim-set in application context
                g.current_user = claim_set
                return func(*args, **kwargs)
            return func_wrapper
        return auth_decorator
