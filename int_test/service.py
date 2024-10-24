from flask import Flask, abort
from jwt_authenticator.authentication_handler import AuthenticationHandler, AuthError

app = Flask(__name__)
app.config["JWKS_URL"] = "https://login.microsoftonline.com/common/discovery/keys"
app.config["AUDIENCE"] = "7d9e0131-09e1-4139-b234-c702a4043afb"
AuthenticationHandler.load_configuration(app)


@app.route('/')
@AuthenticationHandler.requires_auth("Consumer_Admin_development")
def hello_world():
    return "Hello World!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
