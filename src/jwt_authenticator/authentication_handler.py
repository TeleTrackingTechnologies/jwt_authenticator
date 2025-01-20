""" JWT authentication handler for Flask web services"""
import os
from functools import wraps

import jwt
from flask import abort
from flask import g, request, current_app as app
from jwt import PyJWKClient, PyJWK


class AuthError(Exception):
    """ Simple exception object"""

    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code
        Exception.__init__(self)


class AuthenticationHandler:
    """ Basic JWT authentication handler """

    @staticmethod
    def load_configuration(flask_app):
        """ Load configuration from environment variables if set. The application configuration
        values: SECRET and AUDIENCE are expected for this module to work properly.
        Environment variables will override what has already been set in the application config
        (e.g. in config.py) if something has been set. This is helpful when running flask services
        in container environments.
        This method should be called during your application's construction.
         """

        env_secret = os.getenv('JWT_SECRET')
        env_audience = os.getenv('JWT_AUDIENCE')
        env_jwks_url = os.getenv('JWKS_URL')
        env_groups_claim = os.getenv('GROUPS_CLAIM')

        if env_secret:
            flask_app.config['SECRET'] = env_secret

        if env_audience:
            flask_app.config['AUDIENCE'] = env_audience

        if env_jwks_url:
            flask_app.config['JWKS_URL'] = env_jwks_url

        if env_groups_claim:
            flask_app.config['GROUPS_CLAIM'] = env_groups_claim

    @staticmethod
    def generate_auth_token(role_claims, key, algorithm='HS256', headers=None):
        """Generate a JWT token (mostly for testing)"""

        token = jwt.encode(role_claims, key, algorithm, headers=headers)
        return token

    @staticmethod
    def get_jwks_signing_key(jwks_url: str, jwt_token: str) -> PyJWK:
        """ Get the signing key from an OIDC key discovery URL"""

        jwks_client = PyJWKClient(
            uri=jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(jwt_token)
        return signing_key

    @staticmethod
    def validate_and_decode_token(token, key, audience, role_name=None,
                                  algorithms=None):
        """ Valid the token and decode the payload """

        if not algorithms:
            algorithms = ["RS256", "HS256"]
        try:
            claim_set = jwt.decode(
                token,
                key,
                audience=audience,
                algorithms=algorithms)

            group_claims = app.config.get("GROUPS_CLAIM", None)
            if group_claims is not None:
                roles = claim_set[group_claims]

                if role_name:
                    matching_roles = list(
                        filter(lambda x: x.lower() == role_name.lower(), roles))
                    if not matching_roles:
                        raise AuthError({"code": "unauthorized",
                                        "description": "not authorized"}, 401)
        except jwt.ExpiredSignatureError as ex:
            raise AuthError({"code": "token_expired",
                             "description": "token is expired"}, 401) from ex
        except jwt.InvalidAudienceError as ex:
            raise AuthError({"code": "invalid_audience",
                             "description":
                                 "incorrect claims,"
                                 "please check the audience and issuer"}, 401) from ex
        except jwt.InvalidTokenError as ex:
            raise AuthError({"code": "Invalid token",
                             "description":
                                 f"invalid token: {ex}"}, 401) from ex
        except AuthError:
            raise
        # pylint: disable=broad-exception-caught
        except Exception as ex:
            raise AuthError({"code": "unknown error",
                             "description":
                                 "Unable to parse authentication"
                                 " token."}, 401) from ex
        return claim_set

    @staticmethod
    def requires_auth(role_name=None):
        """ Validate access token """

        def auth_decorator(func):  # pragma: no cover
            @wraps(func)
            def func_wrapper(*args, **kwargs):
                try:
                    token = request.headers.get("Authorization", None).split(" ")[1]
                    if not token:
                        abort(401, description="No token")

                    if "JWKS_URL" in app.config:
                        key = AuthenticationHandler.get_jwks_signing_key(
                            app.config["JWKS_URL"],
                            token
                        ).key
                    else:
                        key = app.config['SECRET']
                    claim_set = \
                        AuthenticationHandler.validate_and_decode_token(
                            token,
                            key,
                            app.config['AUDIENCE'],
                            role_name)
                    # if we want to store claim-set in application context
                    g.current_user = claim_set
                except AuthError as ex:
                    abort(ex.status_code, description=ex.error)
                # pylint: disable=broad-exception-caught
                except Exception as ex:
                    abort(500,
                          description=f"Unknown error. {ex}")
                return func(*args, **kwargs)

            return func_wrapper

        return auth_decorator
