import os
import datetime
import unittest
import secrets
from jwt_authenticator.authentication_handler import AuthenticationHandler, AuthError
from flask import Flask


class JwtAuthenticatorTests(unittest.TestCase):
    """ Test fixture for application unit tests"""

    @classmethod
    def setUpClass(cls):
        """Setup for the test class"""

        print("Executing test fixture setup")
        env_modpath = os.environ.get('MODULE_PATH')
        if env_modpath is None:
            cls.mod_path = "../jwt_authenticator"
        else:
            cls.mod_path = env_modpath

        # the path of this file
        cls.this_path = os.path.dirname(__file__)

    def test_generate_and_validate_token_success(self):
        """ Generate and decode a token"""

        audience = 'http://www.service.wingdings.com/'
        roles = {'role': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret)
        decoded_token = AuthenticationHandler.validate_and_decode_token(
            token=token, key=secret,
            audience=audience
        )
        self.assertTrue(decoded_token['role'][0] == 'admin')
        self.assertTrue(decoded_token['role'][1] == 'user')

    def test_generate_and_validate_token_512_success(self):
        """ Generate and decode a token using a different algorithm"""

        audience = 'http://www.service.wingdings.com/'
        roles = {'role': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret, algorithm="HS512")
        decoded_token = AuthenticationHandler.validate_and_decode_token(
            token=token, key=secret,
            audience=audience, algorithms=["HS512"]
        )
        self.assertTrue(decoded_token['role'][0] == 'admin')
        self.assertTrue(decoded_token['role'][1] == 'user')

    def test_validate_token_expired(self):
        """ Expired tokens should throw exceptions"""

        audience = 'http://www.service.wingdings.com/'
        roles = {'role': ['admin', 'user'], 'aud': audience,
                 'exp': datetime.datetime.utcnow() - datetime.timedelta(minutes=15)}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret)
        with self.assertRaises(AuthError):
            _ = AuthenticationHandler.validate_and_decode_token(
                token=token, key=secret,
                audience=audience
            )

    def test_validate_token_role_mismatch(self):
        """ A role is specified and not matched"""

        audience = 'http://www.service.wingdings.com/'
        roles = {'role': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret)
        with self.assertRaises(AuthError):
            _ = AuthenticationHandler.validate_and_decode_token(
                token=token, key=secret, role_name="optimus prime",
                audience=audience)

    def test_validate_token_role_match(self):
        """ A role is specified and matched """

        audience = 'http://www.service.wingdings.com/'
        roles = {'role': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret)
        decoded_token = AuthenticationHandler.validate_and_decode_token(
            token=token, key=secret, role_name="admin",
            audience=audience)
        self.assertTrue(decoded_token['role'][0] == 'admin')
        self.assertTrue(decoded_token['role'][1] == 'user')

    def test_invalid_token_secret_mismatch(self):
        """ Make sure invalid tokens are rejected"""

        audience = 'http://www.service.wingdings.com/'
        roles = {'role': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)
        secret1 = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret)
        with self.assertRaises(AuthError):
            _ = AuthenticationHandler.validate_and_decode_token(
                token=token, key=secret1,
                audience=audience)

    def test_invalid_token_audience_mismatch(self):
        """ Make sure invalid tokens are rejected"""

        audience = 'http://www.service.wingdings.com/'
        roles = {'role': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)
        audience1 = "somebody"

        token = AuthenticationHandler.generate_auth_token(roles, secret)
        with self.assertRaises(AuthError):
            _ = AuthenticationHandler.validate_and_decode_token(
                token=token, key=secret,
                audience=audience1)

    def test_environment_variables_override_config(self):
        """ Specified environment variable settings should override default module config"""

        app = Flask('test.cfg')
        app.config.from_pyfile(f"{self.this_path}/config.py")

        ctx = app.app_context()
        ctx.push()

        os.environ["JWT_SECRET"] = "sed"
        os.environ["JWT_AUDIENCE"] = "larry"

        AuthenticationHandler.load_configuration()

        try:
            self.assertTrue(app.config["SECRET"] == "sed", "Secret does not match")
            self.assertTrue(app.config["AUDIENCE"] == "larry", "Audience does not match")
        finally:
            ctx.pop()

    def test_config_from_file(self):
        """ Specified environment variable settings should override default module config"""

        app = Flask('test.cfg')
        app.config.from_pyfile(f"{self.this_path}/config.py")

        ctx = app.app_context()
        ctx.push()
        AuthenticationHandler.load_configuration()

        try:
            self.assertTrue(app.config["SECRET"] == "foobar", "Secret does not match")
            self.assertTrue(app.config["AUDIENCE"] == "fred", "Audience does not match")
        finally:
            ctx.pop()


