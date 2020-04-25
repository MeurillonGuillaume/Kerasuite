import logging
from os import urandom, listdir, path
import pickledb
from flask import Flask, render_template, redirect, request, session
from werkzeug.utils import secure_filename
from uuid import uuid4
from core.projectmanager import ProjectManager
from core.usermanager import UserManager
from core.runtimemanager import RuntimeManager
from core.modelcomponents import LAYERS, NORMALIZATION_METHODS, LAYER_OPTIONS

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
                 {"admin": {"password": "$2b$12$9PlFNhsAFENiKcsOsqjzAOPwUJyAF6FXCUxxbBHYJAhHai9q8eeCa", "admin": True}})

# Load database
logging.info('Loading database into memory ...')
database = pickledb.load(DATABASE_NAME, True)
project_manager = ProjectManager(database)
user_manager = UserManager(database)
runtime_manager = RuntimeManager(project_manager, app.config['UPLOAD_FOLDER'])

# Global variables
ALLOWED_FILETYPES = ['csv', 'json']


def is_user_logged_in():
    """
    Check if the requester is logged in
    :rtype: bool
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
    :type filename: str
    :rtype: bool
    """
    try:
        return '.' in filename and str(filename).rsplit('.', 1)[1].lower() in ALLOWED_FILETYPES
    except Exception as e:
        logging.error(f'Error in checking if {filename} is allowed: {e}')
        return 0


def post_has_keys(*args):
    """
    Check if a POST request contains all required keys
    :type args: str
    :rtype: bool
    """
    if request.method == 'POST':
        return all(k in request.form for k in args)
    return 0


def get_has_keys(*args):
    """
    Check if required keys are in a GET request and return data if so

    :param args:
    :type: any

    :rtype: dict
    """
    _isvalid, _res = [], {}
    if request.method == 'GET':
        # Check if items are not empty
        for _item in args:
            _data = str(request.args.get(_item))
            if _data is not None and len(_data.strip()) > 0:
                _isvalid.append(1)
            else:
                _isvalid.append(0)
            _res[_item] = str(request.args.get(_item))
        if all(_isvalid):
            return _res
    return None


@app.route('/')
def home():
    """
    Serve the homepage or redirect to the login page
    """
    if is_user_logged_in():
        return render_template('home.html',
                               LoggedIn=session['loggedin'],
                               Projects=project_manager.get_user_projects(),
                               ActiveProjects=runtime_manager.get_running_projects())
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Serve the login page or redirect to home
    """
    if not is_user_logged_in():
        if post_has_keys('password', 'username'):
            if user_manager.attempt_login(request.form['username'], request.form['password']):
                session['loggedin'] = True
                session['username'] = request.form['username']
                if session['username'] == 'admin' and user_manager.admin_has_default_pass():
                    return redirect('/change/password?user=admin')
                return redirect('/')
        return render_template('login.html')
    return redirect('/')


@app.route('/change/password', methods=['GET', 'POST'])
def change_password():
    """
    Change a users password
    """
    if is_user_logged_in():
        data = get_has_keys('user')
        if data is not None and data['user'] == session['username']:
            return render_template('change_password.html', Username=data['user'])
        if post_has_keys('old_password', 'new_password', 'new_password_repeat'):
            old, new, new_repeat = request.form['old_password'], request.form['new_password'], request.form[
                'new_password_repeat']
            user_manager.change_password(old, new, new_repeat)
            return redirect('/logout')
    return redirect('/login')


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
        return render_template('settings.html', LoggedIn=session['loggedin'],
                               IsAdmin=user_manager.has_elevated_rights(),
                               UserList=user_manager.get_users(),
                               Username=session['username'])
    return redirect('/login')


@app.route('/create/project', methods=['GET', 'POST'])
def create_project():
    """
    Create a new project for a certain user
    """
    if is_user_logged_in():
        if post_has_keys('projectdescription', 'projectname'):
            project_manager.create_project(request.form['projectname'],
                                           request.form['projectdescription'])
    return redirect('/login')


@app.route('/drop/project')
def drop_project():
    """
    Drop a project for a certain user
    """
    if is_user_logged_in():
        data = get_has_keys('project')
        if data is not None:
            project_manager.drop_project(data['project'])
            return redirect('/')
    return redirect('/login')


@app.route('/edit/project', methods=['GET', 'POST'])
def edit_project():
    """
    Edit the fields of a project
    """
    if is_user_logged_in():
        if post_has_keys('projectdescription', 'projectname', 'old_projectname'):
            newname = project_manager.update_project(request.form['old_projectname'],
                                                     request.form['projectname'],
                                                     request.form['projectdescription'])
            return redirect(f'/run?project={newname}')
    return redirect('/login')


@app.route('/run')
def run():
    """
    Launch a project or redirect to login
    """
    if is_user_logged_in():
        data = get_has_keys('project')
        if data is not None:
            project = data['project']
            try:
                if project_manager.does_project_exist(project):
                    if project_manager.does_project_have_dataset(project):
                        if not runtime_manager.is_project_running(project):
                            runtime_manager.run_project(project)
                    return render_template('project.html',
                                           Projectname=project,
                                           Projectdescription=project_manager.get_project(project)['description'],
                                           LoggedIn=session['loggedin'],
                                           HasDataset=project_manager.does_project_have_dataset(project),
                                           Dataset=runtime_manager.get_data_head(project),
                                           TrainTestSplit=project_manager.get_preprocessing(project,
                                                                                            'train-test-split'),
                                           RandomState=project_manager.get_preprocessing(project, 'random-state'),
                                           ColumnNames=runtime_manager.get_column_names(project),
                                           Normalizers=NORMALIZATION_METHODS,
                                           DataBalance=runtime_manager.get_data_balance(project),
                                           ModelLayers=LAYERS,
                                           OutputColumns=project_manager.get_preprocessing(project, 'output-columns'),
                                           ProjectModel=project_manager.load_model(project),
                                           LayerOptions=LAYER_OPTIONS)
            except Exception as e:
                logging.error(f'Exception in /run?project{project}: {e}')
    return redirect('/login')


@app.route('/quit')
def quit_project():
    if is_user_logged_in():
        data = get_has_keys('project')
        if data is not None:
            if project_manager.does_project_exist(data['project']):
                runtime_manager.stop_project(data['project'])
                return redirect('/')
    return redirect('/login')


@app.route('/set/project/dataset', methods=['GET', 'POST'])
def set_dataset():
    """
    Set a dataset for a certain project
    """
    if is_user_logged_in():
        if 'dataset' in request.files and post_has_keys('projectname'):
            dataset = request.files['dataset']
            if len(dataset.filename) > 1:
                if is_file_allowed(dataset.filename):
                    file_ext = str(secure_filename(dataset.filename)).rsplit('.', 1)[1]
                    new_filename = str(uuid4())
                    dataset.save(f'{app.config["UPLOAD_FOLDER"]}/{new_filename}.{file_ext}')
                    project_manager.assign_dataset(new_filename, file_ext,
                                                   request.form['projectname'])
                    return redirect(f'/run?project={request.form["projectname"]}')
    return redirect('/login')


@app.route('/set/project/dataset/split', methods=['GET', 'POST'])
def set_dataset_split():
    """
    Assign a certain percentage to split the training & test data with
    """
    if is_user_logged_in():
        if post_has_keys('project', 'train-test-split', 'random-state', 'column-output[]'):
            project_manager.set_preprocessing(request.form['project'],
                                              'train-test-split',
                                              int(request.form['train-test-split']))
            project_manager.set_preprocessing(request.form['project'],
                                              'random-state',
                                              request.form['random-state'])
            project_manager.set_preprocessing(request.form['project'],
                                              'output-columns',
                                              request.form.getlist('column-output[]'))
            return redirect(f'/run?project={request.form["project"]}')
    return redirect('/')


@app.route('/set/column/name', methods=['GET', 'POST'])
def set_column_name():
    """
    Change a column name
    """
    if is_user_logged_in():
        if post_has_keys('project', 'col_name_old', 'col_name_new'):
            runtime_manager.rename_column(request.form['project'],
                                          request.form['col_name_old'],
                                          request.form['col_name_new'])
            return redirect(f'/run?project={request.form["project"]}')
    return redirect('/')


@app.route('/preprocess/columns', methods=['GET', 'POST'])
def preprocess_columns():
    if is_user_logged_in():
        if post_has_keys('project', 'columns[]', 'normalisation-method'):
            runtime_manager.preprocess_project(project_name=request.form['project'],
                                               method=request.form['normalisation-method'],
                                               columns=request.form.getlist('columns[]'))
            return redirect(f'/run?project={request.form["project"]}')
    return redirect('/')


@app.route('/drop/column', methods=['GET', 'POST'])
def drop_column():
    """
    Delete a column
    """
    if is_user_logged_in():
        if post_has_keys('project', 'column'):
            runtime_manager.drop_column(request.form['project'], request.form['column'])
            return redirect(f'/run?project={request.form["project"]}')
    return redirect('/')


@app.route('/replace/dataset/values', methods=['GET', 'POST'])
def replace_dataset_values():
    if is_user_logged_in():
        if post_has_keys('column', 'project', 'value_old', 'value_new'):
            runtime_manager.replace_values(request.form['project'],
                                           request.form['column'],
                                           request.form['value_old'],
                                           request.form['value_new'])
            return redirect(f'/run?project={request.form["project"]}')
    return redirect('/')
    pass


@app.route('/clear/dataset')
def clear_dataset():
    """
    Clear the dataset of a project
    """
    if is_user_logged_in():
        data = get_has_keys('project')
        if data is not None:
            if project_manager.does_project_exist(data['project']):
                if project_manager.does_project_have_dataset(data['project']):
                    project_manager.clear_project_dataset(data['project'])
                    runtime_manager.stop_project(data['project'])
                return redirect(f'/run?project={data["project"]}')
    return redirect('/login')


@app.route('/remove/user')
def remove_user():
    """
    Remove a user from the system
    """
    if is_user_logged_in():
        data = get_has_keys('username')
        if user_manager.has_elevated_rights() and data is not None:
            if user_manager.does_user_exist(data['username']):
                user_manager.delete_user(data['username'])
        return redirect('/settings')
    return redirect('/login')


@app.route('/create/user', methods=['GET', 'POST'])
def create_user():
    """
    Create a new user
    """
    if is_user_logged_in():
        if user_manager.has_elevated_rights():
            if post_has_keys('username', 'password', 'password_repeat'):
                username, password, pass_repeat = request.form['username'], request.form['password'], request.form[
                    'password_repeat']
                if len('username') > 1 and password == pass_repeat:
                    if not user_manager.does_user_exist(username):
                        if user_manager.is_password_strong(password):
                            user_manager.register_user(username, password, False)
        return redirect('/settings')
    return redirect('/login')


@app.route('/op/user')
def op_user():
    """
    Give a user elevated rights
    """
    if is_user_logged_in():
        data = get_has_keys('user')
        if data is not None:
            if user_manager.has_elevated_rights() and user_manager.does_user_exist(data['user']):
                user_manager.change_permissions(data['user'])
        return redirect('/settings')
    return redirect('/login')


@app.route('/create/layer', methods=['GET', 'POST'])
def create_layer():
    """
    Create a new layer in a model
    """
    if is_user_logged_in():
        if post_has_keys('project', 'new-layer'):
            project_manager.add_model_layer(project_name=request.form['project'],
                                            layer_type=request.form['new-layer'])
            return redirect(f'/run?project={request.form["project"]}')
    return redirect('/')


@app.route('/remove/layer')
def remove_layer():
    """
    Remove a layer from a model
    """
    if is_user_logged_in():
        data = get_has_keys('project', 'layer')
        if data is not None:
            project_manager.remove_model_layer(
                project_name=data['project'],
                layer_id=data['layer'])
            return redirect(f'/run?project={data["project"]}')
    return redirect('/')


if __name__ == '__main__':
    app.run(port=4444, host='0.0.0.0')
