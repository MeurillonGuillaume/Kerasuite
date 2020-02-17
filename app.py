import logging
from os import urandom, listdir
from flask import Flask, render_template, redirect, request, session
from libs.authentication import Authentication
from libs.projects import Projects
import pickledb

# Global variables
DATABASE_NAME = 'Kerasuite.db'

# Enable logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__)
app.secret_key = urandom(80)

# Check if the database exists
if DATABASE_NAME not in listdir('.'):
    # Initialise the database with a default user & password (admin - Kerasuite)
    logging.warning('The database does not exist, initialising now ...')
    database = pickledb.load('Kerasuite.db', True)
    database.set('users', {"admin": {"password": "$2b$12$F5t/lNpjbvGMh0m56t1xbe/saHiK.dHKIKif1Q.xOyxcbrr/vKAw."}})

# Load database
logging.info('Loading database into memory ...')
database = pickledb.load(DATABASE_NAME, True)
auth = Authentication(database)
project_client = Projects(database)


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
        return render_template('home.html', LoggedIn=session['loggedin'],
                               Projects=project_client.get_user_projects(session['username']))
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Serve the login page or redirect to home
    """
    if not is_user_logged_in():
        if request.method == 'POST':
            if 'password' in request.form and 'username' in request.form:
                if auth.attempt_login(request.form['username'], request.form['password']):
                    session['loggedin'] = True
                    session['username'] = request.form['username']
                    return redirect('/')
        return render_template('login.html')
    return redirect('/')


@app.route('/logout')
def logout():
    """
    Log a user out and redirect to login
    """
    if is_user_logged_in():
        session['loggedin'] = False
    return redirect('/')


@app.route('/settings')
def settings():
    """
    Return a settings page or redirect to login.
    """
    if is_user_logged_in():
        return render_template('settings.html', LoggedIn=session['loggedin'])
    return redirect('/login')


@app.route('/create/project', methods=['GET', 'POST'])
def create_project():
    """
    Create a new project for a certain user
    """
    if request.method == 'POST':
        if is_user_logged_in():
            if 'projectdescription' in request.form and 'projectname' in request.form:
                project_client.create_project(request.form['projectname'], request.form['projectdescription'],
                                              session['username'])
    return redirect('/login')


@app.route('/drop/project')
def drop_project():
    """
    Drop a project for a certain user
    """
    if is_user_logged_in():
        project = request.args.get('project')
        if project is not None:
            project_client.drop_project(project, session['username'])
        return redirect('/')
    return redirect('/login')


@app.route('/run')
def run():
    if is_user_logged_in():
        project = request.args.get('project')
        if project_client.does_project_exist(project, session['username']):
            return render_template('project.html', Projectname=project, LoggedIn=session['loggedin'])
    return redirect('/login')


if __name__ == '__main__':
    app.run(port=4444)
