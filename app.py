import logging
from os import urandom
from flask import Flask, render_template
from libs.authentication import Authentication
from libs.secrets import Secrets

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = urandom(80)

secrets = Secrets('secrets.json')
auth = Authentication(secrets)


@app.route('/')
def home():
    auth.attempt_login('admin', 'hihi')
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=False, port=4444, host='0.0.0.0')
