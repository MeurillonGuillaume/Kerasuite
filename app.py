from os import urandom, listdir, path
from uuid import uuid4

import absl.logging
from flask import Flask, render_template, redirect
from werkzeug.utils import secure_filename
import pickledb
from core.modelcomponents import LAYERS, NORMALIZATION_METHODS
from core.projectmanager import ProjectManager
from core.runtimemanager import RuntimeManager
from core.usermanager import UserManager
from core.validation import *

# Global variables
DATABASE_NAME = 'Kerasuite.db'

# Enable logging
logging.basicConfig(level=logging.INFO)  # Default logging level

# Remove Tensorflow logging bug
logging.root.removeHandler(absl.logging._absl_handler)
absl.logging._warn_preinit_stderr = False

# Create Flask app
app = Flask(__name__)
app.secret_key = urandom(80)
app.config['UPLOAD_FOLDER'] = path.join(path.dirname(path.realpath(__file__)), 'data')

# Check if the database exists
if DATABASE_NAME not in listdir('.'):
    # Initialise the database with a default user & password (admin - Kerasuite)
    logging.warning('The database does not exist, initialising now ...')
    database = pickledb.load(DATABASE_NAME, auto_dump=True)
    database.set('users',
                 {
                     "admin": {
                         "password": "$2b$12$9PlFNhsAFENiKcsOsqjzAOPwUJyAF6FXCUxxbBHYJAhHai9q8eeCa",
                         "admin": True
                     }
                 })

# Load database
logging.info('Loading database into memory ...')
database = pickledb.load(DATABASE_NAME, auto_dump=True)
project_manager = ProjectManager(database)
user_manager = UserManager(database)
runtime_manager = RuntimeManager(project_manager, app.config['UPLOAD_FOLDER'])


@app.errorhandler(404)
def page_not_found(e):
    """
    Redirect home on non-existing URL

    :param e: The error to handle, print in console
    :type e: str
    """
    logging.error(e)
    return redirect('/')


@app.route('/')
def home():
    """
    Serve the homepage or redirect to the login page
    """
    if is_user_logged_in():
        form = CreateProjectForm()
        logging.debug(f'Loading home for user {session["username"]}')
        return render_template('home.html',
                               LoggedIn=session['loggedin'],
                               Projects=project_manager.get_user_projects(),
                               ActiveProjects=runtime_manager.get_running_projects(),
                               NewProjectForm=form)
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Serve the login page or redirect to home
    """
    form = LoginForm(request.form)
    if not is_user_logged_in():
        if request.method == 'POST' and form.validate():

            if user_manager.attempt_login(form.username.data, form.password.data):
                session['loggedin'] = True
                session['username'] = form.username.data

                if form.username.data == 'admin' and user_manager.admin_has_default_pass():
                    logging.info(f'Admin manager still uses default password, prompting for change')
                    return redirect('/change/password?user=admin')

                return redirect('/')
        else:
            # TODO: proper error handling
            print(form.errors)
        return render_template('login.html', Form=form)
    return redirect('/')


@app.route('/change/password', methods=['GET', 'POST'])
def change_password():
    """
    Change a users password
    """
    form = PasswordUpdateForm(request.form)
    if is_user_logged_in() and request.method == 'POST':
        if form.validate():
            print(form.old_password.data)
            print(form.new_password.data)
            print(form.new_password_validate.data)
            user_manager.change_password(
                old=form.old_password.data,
                new=form.new_password.data,
                new_repeat=form.new_password_validate.data
            )
            return redirect('/logout')
        else:
            # TODO: proper error handling
            print(form.errors)
    else:
        data = get_has_keys('user')
        if data is not None and data['user'] == session['username']:
            logging.info(f"Prompting user {data['user']} to change password")
            return render_template('change_password.html', Username=data['user'], Form=form)
    return redirect('/change/password')


@app.route('/logout')
def logout():
    """
    Log a user out and redirect to login
    """
    if is_user_logged_in():
        session['loggedin'] = False
        logging.debug(f'User {session["username"]} logging out')
    return redirect('/')


@app.route('/settings')
def settings():
    """
    Return a settings page or redirect to login.
    """
    if is_user_logged_in():
        new_user_form = CreateUserForm()
        return render_template('settings.html', LoggedIn=session['loggedin'],
                               IsAdmin=user_manager.has_elevated_rights(),
                               UserList=user_manager.get_users(),
                               Username=session['username'],
                               NewUserForm=new_user_form)
    return redirect('/login')


@app.route('/create/project', methods=['GET', 'POST'])
def create_project():
    """
    Create a new project for a certain user
    """
    if is_user_logged_in():
        form = CreateProjectForm(request.form)
        if request.method == 'POST' and form.validate():
            project_manager.create_project(
                form.project_name.data,
                form.project_description.data
            )
        return redirect('/')
    return redirect('/login')


@app.route('/drop/project')
def drop_project():
    """
    Drop a project for a certain user
    """
    if is_user_logged_in():
        data = get_has_keys('project')
        if data is not None:
            logging.info(f'User {session["username"]} dropped project {data["project"]}')
            project_manager.drop_project(data['project'])
            return redirect('/')
    return redirect('/login')


@app.route('/edit/project', methods=['GET', 'POST'])
def edit_project():
    """
    Edit the fields of a project
    """
    form = EditProjectForm(request.form)
    if is_user_logged_in() and form.validate() and request.method == 'POST':
        newname = project_manager.update_project(form.project_oldname.data,
                                                 form.project_newname.data,
                                                 form.project_description.data)
        return redirect(f'/run?project={newname}')
    return redirect('/login')


@app.route('/run')
def run():
    """
    Launch a project or redirect to login
    """
    edit_form = EditProjectForm()
    preprocessing_form = PreprocessingForm()
    rename_form = RenameColumnForm()
    normalization_form = NormalizeForm()
    drop_form = DropColumnForm()
    replace_form = ReplaceDataForm()
    create_layer_form = CreateLayerForm()

    if is_user_logged_in():
        data = get_has_keys('project')
        err = get_has_keys('error')
        if data is not None:
            project = data['project']
            if project_manager.does_project_exist(project):
                if project_manager.does_project_have_dataset(project):
                    if not runtime_manager.is_project_running(project):
                        runtime_manager.run_project(project)
                logging.info(f'Loading project {data["project"]} for user {session["username"]}')

                columns = runtime_manager.get_column_names(project)
                preprocessing_form.set_column_names(columns)
                preprocessing_form.set_selected_columns(project_manager.get_preprocessing(project, 'output-columns'))
                rename_form.set_old_columns(columns)
                normalization_form.set_column_names(columns)
                drop_form.set_column_names(columns)
                replace_form.set_column_names(columns)

                return render_template('project.html',
                                       Projectname=project,
                                       Projectdescription=project_manager.get_project(project)['description'],
                                       LoggedIn=session['loggedin'],
                                       HasDataset=project_manager.does_project_have_dataset(project),
                                       Dataset=runtime_manager.get_data_head(project),
                                       TrainTestSplit=project_manager.get_preprocessing(project,
                                                                                        'train-test-split'),
                                       RandomState=project_manager.get_preprocessing(project, 'random-state'),
                                       ColumnNames=columns,
                                       DataBalance=runtime_manager.get_data_balance(project),
                                       ModelLayers=LAYERS,
                                       ProjectModel=project_manager.load_model(project),
                                       LayerOptions=LAYER_OPTIONS,
                                       TrainScoring=project_manager.load_model_scoring(
                                           project_name=project,
                                           scoring_source=project_manager.SCORING_TRAIN),
                                       TestScoring=project_manager.load_model_scoring(
                                           project_name=project,
                                           scoring_source=project_manager.SCORING_TEST),
                                       Error=err['error'],
                                       ModifyProjectForm=edit_form,
                                       PreprocessingForm=preprocessing_form,
                                       RenameForm=rename_form,
                                       NormalizationForm=normalization_form,
                                       Normalizers=NORMALIZATION_METHODS,
                                       DropForm=drop_form,
                                       ReplaceForm=replace_form,
                                       CreateLayerForm=create_layer_form)

    return redirect('/login')


@app.route('/quit')
def quit_project():
    """
    Remove a project from the runtime session
    """
    if is_user_logged_in():
        data = get_has_keys('project')
        if data is not None:
            if project_manager.does_project_exist(data['project']):
                runtime_manager.stop_project(data['project'])
                logging.info(f"Shutdown project {data['project']} for user {session['username']}")
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
                    logging.info(f'Project {request.form["projectname"]} received a new dataset')
                    return redirect(f'/run?project={request.form["projectname"]}')
    return redirect('/login')


@app.route('/set/project/dataset/split', methods=['GET', 'POST'])
def set_dataset_split():
    """
    Assign a certain percentage to split the training & test data with
    """
    if is_user_logged_in() and request.method == 'POST':
        form = PreprocessingForm(request.form)
        form.set_column_names(runtime_manager.get_column_names(request.form['project']))
        if form.validate():
            project_manager.set_preprocessing(form.project.data,
                                              'train-test-split',
                                              int(form.train_test_split.data))
            project_manager.set_preprocessing(form.project.data,
                                              'random-state',
                                              int(form.random_state.data))
            project_manager.set_preprocessing(form.project.data,
                                              'output-columns',
                                              form.column_output.data)
            return redirect(f'/run?project={form.project.data}')
    return redirect('/')


@app.route('/set/column/name', methods=['GET', 'POST'])
def set_column_name():
    """
    Change a column name
    """
    if is_user_logged_in() and request.method == 'POST':
        form = RenameColumnForm(request.form)
        form.set_old_columns(runtime_manager.get_column_names(request.form['project']))
        if form.validate():
            runtime_manager.rename_column(form.project.data,
                                          form.old_col_name.data,
                                          form.new_col_name.data)
            return redirect(f'/run?project={form.project.data}')
        else:
            print(form.errors)
    return redirect('/')


@app.route('/normalize/columns', methods=['GET', 'POST'])
def normalize_columns():
    if is_user_logged_in() and request.method == 'POST':
        form = NormalizeForm(request.form)
        form.set_column_names(runtime_manager.get_column_names(request.form['project']))
        form.set_method_choises(NORMALIZATION_METHODS)
        if form.validate():
            runtime_manager.preprocess_project(project_name=form.project.data,
                                               method=form.method.data,
                                               columns=form.columns.data)
            return redirect(f'/run?project={form.project.data}')
        else:
            print(form.errors)
    return redirect('/')


@app.route('/drop/column', methods=['GET', 'POST'])
def drop_column():
    """
    Delete a column
    """
    if is_user_logged_in() and request.method == 'POST':
        form = DropColumnForm(request.form)
        form.set_column_names(runtime_manager.get_column_names(request.form['project']))

        if form.validate():
            runtime_manager.drop_column(form.project.data, form.column.data)
            return redirect(f'/run?project={form.project.data}')
    return redirect('/')


@app.route('/replace/dataset/values', methods=['GET', 'POST'])
def replace_dataset_values():
    if is_user_logged_in() and request.method == 'POST':
        form = ReplaceDataForm(request.form)
        form.set_column_names(runtime_manager.get_column_names(request.form['project']))

        if form.validate():
            runtime_manager.replace_values(form.project.data,
                                           form.column.data,
                                           form.value_old.data,
                                           form.value_new.data)
            return redirect(f'/run?project={form.project.data}')
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
    if is_user_logged_in() and request.method == 'POST':
        if user_manager.has_elevated_rights():
            form = CreateUserForm(request.form)
            if form.validate():
                if not user_manager.does_user_exist(form.username.data):
                    user_manager.register_user(form.username.data, form.password.data, False)
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
    layer_forms = {'Dense': AddDenseLayerForm, 'Dropout': AddDropoutLayerForm}

    if is_user_logged_in() and request.method == 'POST':
        # Validate a baseform first, which contains the project name, layer type & description
        baseform = CreateLayerForm(request.form)
        baseform.new_layer.data = baseform.new_layer_name.data
        if baseform.validate():
            # Load the datafrom which fits the specific layer type
            dataform = layer_forms[baseform.new_layer.data](request.form)
            if dataform.validate():
                layer_data = get_layer_params(form_data=dataform, layer_type=baseform.new_layer.data)
                project_manager.add_model_layer(project_name=baseform.project.data,
                                                layer_type=baseform.new_layer.data,
                                                layer_params=layer_data,
                                                description=baseform.layer_description.data)
                return redirect(f'/run?project={baseform.project.data}')
            else:
                print(dataform.errors)
        else:
            print(baseform.errors)
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


@app.route('/train/model')
def train_model():
    """
    Train a model for the current project
    """
    if is_user_logged_in():
        data = get_has_keys('project')
        if data is not None:
            try:
                runtime_manager.split_project_dataset(data['project'])
                runtime_manager.train_project_model(data['project'])
                return redirect(f'/run?project={data["project"]}')
            except Exception as e:
                logging.error(f'Failed to train project {data["project"]}: {e}')

                # Check where the error happened
                err = project_manager.validate_training_settings(data['project'])
                if err is not None:
                    return redirect(f'/run?project={data["project"]}&error={err}')
    return redirect('/')


if __name__ == '__main__':
    app.run(port=4444, host='0.0.0.0', debug=True)
