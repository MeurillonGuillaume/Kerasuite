import logging
from os import urandom, listdir, path
import pickledb
from flask import Flask, render_template, redirect, request, session
from werkzeug.utils import secure_filename
from uuid import uuid4
from libs.projectmanager import ProjectManager
from libs.usermanager import UserManager

# Global variables
DATABASE_NAME = 'Kerasuite.db'

# Enable logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__)
app.secret_key = urandom(80)
app.config['UPLOAD_FOLDER'] = path.join(path.dirname(path.realpath(__file__)), 'data')

# Check if the database exists
if DATABASE_NAME not in listdir('.'):
    # Initialise the database with a default user & password (admin - Kerasuite)
    logging.warning('The database does not exist, initialising now ...')
    database = pickledb.load('Kerasuite.db', True)
    database.set('users',
                 {"admin": {"password": "$2b$12$F5t/lNpjbvGMh0m56t1xbe/saHiK.dHKIKif1Q.xOyxcbrr/vKAw.", "admin": True}})

# Load database
logging.info('Loading database into memory ...')
database = pickledb.load(DATABASE_NAME, True)
project_manager = ProjectManager(database)
user_manager = UserManager(database)

# Global variables
ALLOWED_FILETYPES = ['csv', 'json']


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


def is_file_allowed(filename):
    """
    Check if a filetype is allowed
    """
    try:
        return '.' in filename and str(filename).rsplit('.', 1)[1].lower() in ALLOWED_FILETYPES
    except Exception as e:
        return 0


@app.route('/')
def home():
    """
    Serve the homepage or redirect to the login page
    """
    if is_user_logged_in():
        return render_template('home.html', LoggedIn=session['loggedin'],
                               Projects=project_manager.get_user_projects(session['username']))
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Serve the login page or redirect to home
    """
    if not is_user_logged_in():
        if request.method == 'POST':
            if 'password' in request.form and 'username' in request.form:
                if user_manager.attempt_login(request.form['username'], request.form['password']):
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
        print(user_manager.get_users(session['username']))
        return render_template('settings.html', LoggedIn=session['loggedin'],
                               IsAdmin=user_manager.has_elevated_rights(session['username']),
                               UserList=user_manager.get_users(session['username']),
                               Username=session['username'])
    return redirect('/login')


@app.route('/create/project', methods=['GET', 'POST'])
def create_project():
    """
    Create a new project for a certain user
    """
    if request.method == 'POST' and is_user_logged_in():
        if 'projectdescription' in request.form and 'projectname' in request.form:
            project_manager.create_project(request.form['projectname'],
                                           request.form['projectdescription'],
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
            project_manager.drop_project(project, session['username'])
        return redirect('/')
    return redirect('/login')


@app.route('/edit/project', methods=['GET', 'POST'])
def edit_project():
    """
    Edit the fields of a project
    """
    if is_user_logged_in() and request.method == 'POST':
        if 'projectdescription' in request.form and 'projectname' in request.form and 'old_projectname' in request.form:
            newname = project_manager.update_project(request.form['old_projectname'],
                                                     request.form['projectname'],
                                                     request.form['projectdescription'],
                                                     session['username'])
            return redirect(f'/run?project={newname}')
    return redirect('/login')


@app.route('/run')
def run():
    """
    Launch a project or redirect to login
    """
    if is_user_logged_in():
        project = request.args.get('project')
        if project_manager.does_project_exist(project, session['username']):
            if project_manager.does_project_have_dataset(project, session['username']):
                # TODO: load dataset in memory
                ...
            return render_template('project.html',
                                   Projectname=project,
                                   Projectdescription=project_manager.get_project(
                                       project, session['username'])['description'],
                                   LoggedIn=session['loggedin'],
                                   HasDataset=project_manager.does_project_have_dataset(project, session['username']))
    return redirect('/login')


@app.route('/set/project/dataset', methods=['GET', 'POST'])
def set_dataset():
    """
    Set a dataset for a certain project
    """
    if is_user_logged_in() and request.method == 'POST':
        if 'dataset' in request.files and 'projectname' in request.form:
            dataset = request.files['dataset']
            if len(dataset.filename) > 1:
                if is_file_allowed(dataset.filename):
                    file_ext = str(secure_filename(dataset.filename)).rsplit('.', 1)[1]
                    new_filename = str(uuid4())
                    dataset.save(f'{app.config["UPLOAD_FOLDER"]}/{new_filename}.{file_ext}')
                    project_manager.assign_dataset(new_filename, file_ext,
                                                   request.form['projectname'],
                                                   session['username'])
                    return redirect(f'/run?project={request.form["projectname"]}')
    return redirect('/login')


@app.route('/clear/dataset')
def clear_dataset():
    """
    Clear the dataset of a project
    """
    if is_user_logged_in():
        project = request.args.get('project')
        if project_manager.does_project_exist(project, session['username']):
            if project_manager.does_project_have_dataset(project, session['username']):
                project_manager.clear_project_dataset(project, session['username'])
            return redirect(f'/run?project={project}')
    return redirect('/login')


@app.route('/remove/user')
def remove_user():
    """
    Remove a user from the system
    """
    if is_user_logged_in():
        username = request.args.get('username')
        if user_manager.has_elevated_rights(session['username']) and username is not None and len(username) > 1:
            if user_manager.does_user_exist(username):
                user_manager.delete_user(username)
        return redirect('/settings')
    return redirect('/login')


if __name__ == '__main__':
    app.run(port=4444, host='0.0.0.0')
