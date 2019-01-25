https://travis-ci.com/mikenac/jwt_authenticator.svg?branch=master

# jwt_authenticator

jwt_authenticator is a simply python library for adding JWT token authentication/authorization in flask web sites/services. It controls access either by checking for just a validated token, or optionally, a single role claim from the token. Access is controlled by decorating the endpoint functions with an attribute.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install jwt_authenticator.

```bash
pip install jwt_authenticator
```

## Usage
In the main application initialization area

```python
from Flask import Flask
from jwt_authenticator import AuthenticationHandler

APP = Flask(__name__)
AuthenticationHandler.load_configuration()
```
In the endpoints

```python
from jwt_authenticator import AuthenticationHandler, AuthError

@api.route('/<name>', methods=['GET'])
@AuthenticationHandler.requires_auth("admin")
def get_one(name):
    return f"Hello {name}"

@api.route('/<name>', methods=['GET'])
@AuthenticationHandler.requires_auth()
def get_one(name):
    return f"Hello {name}"
```

## Configuration
jwt_authenticator requires two configuration values to work. These can be specified either in the normal Flask application configuration or as environment variables. Environment variable values will override application configuration values, when

```python
AuthenticationHanlder.load_configuration()
```
is called.

### APP.config (i.e. flask application configuration)

* SECRET - the key used to sign the JWT token
* AUDIENCE - the audience claim used in the JWT token

### Environment Variables

* JWT_SECRET - will override SECRET
* JWT_AUDIENCE - will override AUDIIENCE


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Building
* Requires 'make'

```bash
make init
make test
make package
```

## License
[MIT](https://choosealicense.com/licenses/mit/)

