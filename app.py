import logging
from os import urandom
from flask import Flask, render_template, redirect, request, session
from libs.authentication import Authentication
from libs.secrets import Secrets

# Enable logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__)
app.secret_key = urandom(80)

# Load suite secrets
secrets = Secrets('secrets.json')
auth = Authentication(secrets)


def is_user_logged_in():
    """
    Check if the requester is logged in
    :return: Boolean: True or False
    """
    try:
        return session['loggedin']
    except Exception as e:
        logging.debug(f'Session not yet created, creating empty. {e}')
        session['loggedin'] = False
        return 0


@app.route('/')
def home():
    """
    Serve the homepage or redirect to the login page
    """
    if is_user_logged_in():
        return render_template('home.html', LoggedIn=True,
                               Projects=[{"name": "Hello, World!", "description": "Some text about this project"},
                                         {"name": "Project 2", "description": "Some text about this project"},
                                         {"name": "Project Kerasuite", "description": "Some text about this project"},
                                         {"name": "Yet another great project",
                                          "description": "Some text about this project"},
                                         {"name": "This is fine", "description": "Some text about this project"}])
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Serve the login page or redirect to home
    """
    if request.method == 'POST':
        if 'password' in request.form and 'username' in request.form:
            if auth.attempt_login(request.form['username'], request.form['password']):
                session['loggedin'] = True
                return redirect('/')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    Log a user out and redirect to login
    """
    if is_user_logged_in():
        session['loggedin'] = False
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=False, port=4444, host='0.0.0.0')
