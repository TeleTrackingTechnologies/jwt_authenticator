import datetime
import json
import os
import secrets
import unittest
from datetime import timezone

from flask import Flask
from jwt.utils import base64url_encode

from jwt_authenticator.authentication_handler import AuthenticationHandler, AuthError
from key_utils import public_key, private_key


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
        app = Flask('test.cfg')
        app.config.from_pyfile(f"{self.this_path}/config.py")

        ctx = app.app_context()
        ctx.push()

        audience = 'http://www.service.wingdings.com/'
        roles = {'groups': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret)
        decoded_token = AuthenticationHandler.validate_and_decode_token(
            token=token, key=secret,
            audience=audience,
            algorithms=["HS256"]
        )
        self.assertTrue(decoded_token['groups'][0] == 'admin')
        self.assertTrue(decoded_token['groups'][1] == 'user')

    def test_generate_and_validate_token_512_success(self):
        """ Generate and decode a token using a different algorithm"""

        app = Flask('test.cfg')
        app.config.from_pyfile(f"{self.this_path}/config.py")

        ctx = app.app_context()
        ctx.push()

        audience = 'http://www.service.wingdings.com/'
        roles = {'groups': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret,
                                                          algorithm="HS512")
        decoded_token = AuthenticationHandler.validate_and_decode_token(
            token=token, key=secret,
            audience=audience, algorithms=["HS512"]
        )
        self.assertTrue(decoded_token['groups'][0] == 'admin')
        self.assertTrue(decoded_token['groups'][1] == 'user')

    def test_validate_token_expired(self):
        """ Expired tokens should throw exceptions"""

        audience = 'http://www.service.wingdings.com/'
        roles = {'groups': ['admin', 'user'], 'aud': audience,
                 'exp': datetime.datetime.now(timezone.utc) - datetime.timedelta(minutes=15)}
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
        roles = {'groups': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret)
        with self.assertRaises(AuthError):
            _ = AuthenticationHandler.validate_and_decode_token(
                token=token, key=secret, role_name="optimus prime",
                audience=audience)

    def test_validate_token_role_match(self):
        """ A role is specified and matched """

        app = Flask('test.cfg')
        app.config.from_pyfile(f"{self.this_path}/config.py")

        ctx = app.app_context()
        ctx.push()

        audience = 'http://www.service.wingdings.com/'
        roles = {'groups': ['admin', 'user'], 'aud': audience}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(roles, secret)
        decoded_token = AuthenticationHandler.validate_and_decode_token(
            token=token, key=secret, role_name="admin",
            audience=audience)
        self.assertTrue(decoded_token['groups'][0] == 'admin')
        self.assertTrue(decoded_token['groups'][1] == 'user')

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

    def test_get_jwks_token_signer(self):
        """ Test getting a key issuer from a public URL """

        app = Flask('test.cfg')
        app.config.from_pyfile(f"{self.this_path}/config.py")

        ctx = app.app_context()
        ctx.push()

        pubkey_n = base64url_encode(
            public_key.public_numbers().n.to_bytes(
                (public_key.key_size + 7) // 8, 'big'))
        pubkey_e = base64url_encode(
                public_key.public_numbers().e.to_bytes(4, 'big'))

        jwk = {
            "kty": "RSA",
            "kid": "kid1",
            "use": "sig",
            "alg": "RS256",
            "n": pubkey_n.decode("utf-8"),
            "e": pubkey_e.decode("utf-8")
        }
        keys = {
            "keys": [jwk, ]
        }
        with open('keys.json', 'w') as f:
            json.dump(keys, f)

        key_path = os.getcwd() + "/keys.json"
        print("KEY_PATH=" + key_path)

        jwks_url = f"file://{key_path}"
        audience = 'http://www.service.wingdings.com/'
        roles = {'groups': ['admin', 'user'], 'aud': audience}
        token = AuthenticationHandler.generate_auth_token(roles, private_key, "RS256",
                                                          headers={"kid": "kid1"})

        key = AuthenticationHandler.get_jwks_signing_key(jwks_url, token)
        claims = AuthenticationHandler.validate_and_decode_token(token, key,
                                                                 audience=audience)
        self.assertTrue(claims)

    def test_environment_variables_override_config(self):
        """ Specified environment variable settings should override default module config"""

        app = Flask('test.cfg')
        app.config.from_pyfile(f"{self.this_path}/config.py")

        ctx = app.app_context()
        ctx.push()

        os.environ["JWT_SECRET"] = "sed"
        os.environ["JWT_AUDIENCE"] = "larry"
        os.environ["JWKS_URL"] = "http://foo.bar"

        AuthenticationHandler.load_configuration(app)

        try:
            self.assertTrue(app.config["SECRET"] == "sed", "Secret does not match")
            self.assertTrue(app.config["AUDIENCE"] == "larry",
                            "Audience does not match")
            self.assertTrue(app.config["JWKS_URL"] == "http://foo.bar",
                            "JWKS url not match")
        finally:
            ctx.pop()

    def test_config_from_file(self):
        """ Specified environment variable settings should override default module
        config"""

        app = Flask('test.cfg')
        app.config.from_pyfile(f"{self.this_path}/config.py")

        ctx = app.app_context()
        ctx.push()
        AuthenticationHandler.load_configuration(app)

        try:
            self.assertTrue(app.config["SECRET"] == "foobar", "Secret does not match")
            self.assertTrue(app.config["AUDIENCE"] == "fred", "Audience does not match")
            self.assertTrue(app.config["JWKS_URL"] == "http://bar.foo",
                            "JWKS url not match")
        finally:
            ctx.pop()

    def test_validate_token_without_role_group(self):
        """Decode token that does not have role groups"""

        app = Flask('test.cfg')
        app.config.from_pyfile(f"{self.this_path}/config.py")
        app.config.pop('GROUPS_CLAIM')

        ctx = app.app_context()
        ctx.push()

        audience = 'http://www.service.wingdings.com/'
        claims = {'aud': audience}
        secret = secrets.token_urlsafe(32)

        token = AuthenticationHandler.generate_auth_token(claims, secret)
        decoded_token = AuthenticationHandler.validate_and_decode_token(
            token=token, key=secret,
            audience=audience,
            algorithms=["HS256"]
        )
        self.assertTrue(decoded_token['aud'] == audience)