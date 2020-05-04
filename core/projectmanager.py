import logging
import pathlib
import time
from pickledb import PickleDB
from os import remove
from uuid import uuid4
from flask import session


class ProjectManager:
    SCORING_TEST = 'test'
    SCORING_TRAIN = 'train'
    __PREPROCESSING_OPTIONS = {
        'train-test-split': str,
        'random-state': int,
        'output-columns': list
    }
    __MODEL_OPTIONS = {
        'epochs': int,
        'batch-size': int,
        'layers': list,
        'validation-split': float
    }

    def __init__(self, db_instance):
        """
        Initialise the database connector

        :param db_instance: The PickleDB connector instance
        :type db_instance: PickleDB
        """
        self.__db_client = db_instance

    def get_user_projects(self):
        """
        Get all projects for a certain user

        :returns: a list of projects, or an empty list if no projects are available
        :rtype: list
        """
        try:
            return self.get_all_projects()[session['username']]
        except Exception as e:
            logging.error(f'Something went wrong requesting the projects for user {session["username"]}: {e}')
            return []

    def create_project(self, name, description):
        """
        Create a new project for a certain user

        :param name: The name to give to this project
        :type name: str

        :param description: A description about the project
        :type description: str

        """
        projects = self.get_all_projects()
        if not projects:
            projects = {}

        if session['username'] not in projects:
            projects[session['username']] = []

        if not self.does_project_exist(name):
            if session['username'] in projects.keys():
                projects[session['username']].append({
                    'name': name,
                    'description': description
                })
            else:
                projects[session['username']] = [{
                    'name': name,
                    'description': description
                }]
            self.__db_client.set('projects', projects)
            self.__db_client.dump()
            self.create_model(project_name=name)
            logging.info(f"Created project {name} for user {session['username']}")

    def get_all_projects(self):
        """
        Request all projects

        :rtype: dict
        """
        return self.__db_client.get('projects')

    def get_project(self, name):
        """
        Request data for a single project

        :param name: The name of the project to retrieve
        :type name: str

        :rtype: dict
        """
        projects = self.get_all_projects()
        if not isinstance(projects, bool):
            projects = projects[session['username']]
            for project in projects:
                if project['name'] == name:
                    return project
        return 0

    def drop_project(self, name):
        """
        Remove 1 specific project

        :param name: The name of the project to delete
        :type name: str
        """
        # Remove project from project list
        projects = self.get_all_projects()
        project_to_trash = self.get_project(name)
        projects[session['username']].remove(project_to_trash)
        self.__db_client.set('projects', projects)
        self.__db_client.dump()
        # Remove dataset from database entry
        self.clear_project_dataset(project_to_trash['name'])

    def update_project(self, old_name, new_name, description):
        """
        Change the name and/or description of a project if possible

        :param old_name: The current project name
        :type old_name: str

        :param new_name: The new name to assign to this project
        :type new_name: str

        :param description: An optional updated description for the project
        :type description: str
        """
        user_projects = self.get_user_projects()
        if self.does_project_exist(new_name):
            if old_name != new_name:
                return old_name
        # Change settings for the general project
        for project in user_projects:
            if project['name'] == old_name:
                user_projects[user_projects.index(project)] = {'name': new_name, 'description': description}
                # Change the name in the database under project datasets as well
                if self.does_project_have_dataset(old_name):
                    self.reassign_dataset(old_name, new_name)

        projects = self.get_all_projects()
        projects[session['username']] = user_projects
        self.__db_client.set('projects', projects)
        self.__db_client.dump()
        return new_name

    def does_project_exist(self, project_name):
        """
        Check if a project exists or not

        :param project_name: The project to check existence of
        :type project_name: str

        :rtype: bool
        """
        p = self.get_project(project_name)
        if p is not 0:
            return 1
        return 0

    def get_all_datasets(self):
        """
        Retrieve all datasets

        :rtype: dict
        """
        return self.__db_client.get('datasets')

    def assign_dataset(self, name, data_type, project_name):
        """
        Assign a dataset to a users project

        :param name: The name of the dataset, an UUID4
        :type name: str

        :param data_type: The type of dataset, currently only JSON and CSV
        :type data_type: str

        :param project_name: The name of the project
        :type project_name: str
        """
        data = self.get_all_datasets()
        if not data:
            data = {session['username']: []}

        i = 0
        for project in data[session['username']]:
            if project['projectname'] == project_name:
                data[session['username']][i] = {
                    'dataset': name,
                    'datatype': data_type,
                    'preprocessing': {
                        'train-test-split': 70,
                        'random-state': 0,
                        'output-columns': []
                    }
                }
                self.__db_client.set('datasets', data)
                self.__db_client.dump()
                return 1
            i += 1
        data[session['username']].append({
            'projectname': project_name,
            'datatype': data_type,
            'dataset': name,
            'preprocessing': {
                'train-test-split': 70,
                'random-state': 0,
                'output-columns': []
            }
        })
        self.__db_client.set('datasets', data)

    def reassign_dataset(self, old_name, new_name):
        """
        Move the dataset from one project to another, used when renaming a project

        :param old_name: Current projectname the dataset is assigned to
        :type old_name: str

        :param new_name: New projectname to assign the dataset to
        :type new_name: str
        """
        data = self.get_all_datasets()
        for i in range(len(data[session['username']])):
            if data[session['username']][i]['projectname'] == old_name:
                data[session['username']][i]['projectname'] = new_name
        self.__db_client.set('datasets', data)
        self.__db_client.dump()

    def does_project_have_dataset(self, project_name):
        """
        Check if a project does have a dataset assigned

        :param project_name: The project to check
        :type project_name: str
        """
        data = self.get_all_datasets()
        if data:
            if session['username'] in data.keys():
                for project in data[session['username']]:
                    if project['projectname'] == project_name:
                        if project['dataset'] is not None and project['datatype'] is not None:
                            return 1
        return 0

    def get_project_dataset(self, project_name):
        """
        Get the name of the dataset

        :param project_name: The project to retrieve
        :type project_name: str
        """
        data = self.get_all_datasets()
        if data:
            if session['username'] in data.keys():
                for project in data[session['username']]:
                    if project['projectname'] == project_name:
                        return f'{project["dataset"]}.{project["datatype"]}'
        return None

    def clear_project_dataset(self, projectname):
        """
        Delete the dataset from a project

        :param projectname: The project to delete
        :type projectname: str
        """
        data = self.get_all_datasets()
        if data:
            for i in range(len(data[session['username']])):
                if data[session['username']][i]['projectname'] == projectname:
                    dataset = self.get_project_dataset(projectname)
                    remove(f'{pathlib.Path(__file__).parent.parent.absolute()}/data/{dataset}')
                    data[session['username']].remove(data[session['username']][i])
                    self.__db_client.set('datasets', data)
                    self.__db_client.dump()

    def set_preprocessing(self, project, param, value):
        """
        Set a preprocessing value

        :param project: The project to set preprocessing parameter from
        :type project: str

        :param param: The parameter name to set
        :type param: str

        :param value: The value to be set
        :type value: Any

        :rtype: bool
        """
        try:
            data = self.get_all_datasets()
            for _project in data[session['username']]:
                if _project['projectname'] == project:
                    logging.info(f'User {session["username"]} set {param} to {value} for {project}')
                    # Attempt to store non-strings as their correct type
                    try:
                        _project['preprocessing'][param] = eval(value)
                    except Exception as e:
                        logging.warning(
                            f"Could not store preprocessing parameter as evaluated datatype, defaulting to String: {e}")
                        _project['preprocessing'][param] = value
                    self.__db_client.set('datasets', data)
                    return 1
            return 0
        except Exception as e:
            logging.error(f'Failed to set dataset percentage for {project} by user {session["username"]}: {e}')
            return 0

    def get_preprocessing(self, project_name, param_name):
        """
        Request a preprocessing value

        :param project_name: The project to request from
        :type project_name: str

        :param param_name: The parameter to request
        :type param_name: str

        :rtype: float
        """
        try:
            data = self.get_all_datasets()
            for _project in data[session['username']]:
                if _project['projectname'] == project_name:
                    return _project['preprocessing'][param_name]
        except Exception as e:
            logging.error(
                f'Failed to retrieve project {project_name} train_test_split data for user {session["username"]}: {e}')
            return None

    def get_all_models(self):
        """
        Load all models that have been created

        :rtype: dict
        """
        try:
            return self.__db_client.get('models')
        except Exception as e:
            logging.error(f'Error loading models: {e}')

    def create_model(self, project_name):
        """
        Create a new model dataholder in the database for a project

        :param project_name: The project to create a model for
        :type project_name: str
        """
        models = self.get_all_models()

        # Handle if models is empty
        if not models:
            models = {}

        # Handle if user has no models yet
        if session['username'] not in models:
            models[session['username']] = {}

        # Check if project has a model defined
        if project_name not in models[session['username']]:
            models[session['username']][project_name] = {
                'epochs': 5,
                'batch-size': 10,
                'layers': [],
                'timestamp': time.time(),
                'validation-split': 0.15,
                'test_score': {}
            }
            # TODO: handle creating a new model + store old model in database
        self.__db_client.set('models', models)

    def add_model_layer(self, project_name, layer_type, layer_params, description):
        """
        Create a new layer in a model

        :param project_name: The project that will get an updated model
        :type project_name: str

        :param layer_type: The layer to add to the model
        :type layer_type: str

        :param layer_params: A dictionary of layer parameters
        :type layer_params: dict

        :param description: Extra information about this layer
        :type description: str
        """
        models = self.get_all_models()

        # Create a base model if it doesn't exist
        if not models or session['username'] not in models or project_name not in models[session['username']]:
            self.create_model(project_name)
            models = self.get_all_models()

        # Check the layer count for order
        layer_number = len(models[session['username']][project_name]['layers'])

        # Add new layer
        models[session['username']][project_name]['layers'].append({
            'layerType': layer_type,
            'layerId': str(uuid4()),
            'order': layer_number,
            'parameters': layer_params,
            'description': description
        })
        self.__db_client.set('models', models)

    def remove_model_layer(self, project_name, layer_id):
        """
        Remove a layer from a model

        :param project_name:
        :type project_name: str

        :param layer_id:
        :type layer_id: str

        :rtype: bool
        """
        models = self.get_all_models()

        # Check if models exist
        if not models or session['username'] not in models or project_name not in models[session['username']]:
            return 0

        # Remove layer
        for layer in models[session['username']][project_name]['layers']:
            if layer['layerId'] == layer_id:
                models[session['username']][project_name]['layers'].remove(layer)
                self.__db_client.set('models', models)
                return 1
        return 0

    def load_model(self, project_name):
        """
        Load a model for a project from the database

        :param project_name: The project of which to load the model
        :type project_name: str

        :rtype: dict
        """
        models = self.get_all_models()
        if not models or session['username'] not in models or project_name not in models[session['username']]:
            return None
        else:
            return models[session['username']][project_name]

    def store_model_scoring(self, project_name, scoring, scoring_source):
        """
        Write test-results to the database

        :param project_name: The project which model has been tested
        :type project_name: str

        :param scoring: A dictionary with model scoring metrics
        :type scoring: dict

        :param scoring_source: The source of scoring metrics
        :type scoring_source: str
        """
        models = self.get_all_models()
        # Check if models exist
        if not models or session['username'] not in models or project_name not in models[session['username']]:
            return 0

        if scoring_source in [self.SCORING_TEST, self.SCORING_TRAIN]:
            models[session['username']][project_name][f'{scoring_source}_score'] = scoring
            self.__db_client.set('models', models)
            return 1
        return 0

    def load_model_scoring(self, project_name, scoring_source):
        """
        Retrieve scoring for a model

        :param project_name: The project to get model scoring from
        :type project_name: str

        :param scoring_source: The source of the scoring (train or test)
        :type scoring_source: str

        :rtype: dict
        """
        models = self.get_all_models()
        # Check if models exist
        if not models or session['username'] not in models or project_name not in models[session['username']]:
            return None

        if scoring_source in [ProjectManager.SCORING_TEST, ProjectManager.SCORING_TRAIN]:
            try:
                return models[session['username']][project_name][f'{scoring_source}_score']
            except Exception as e:
                logging.error(f'Could not load model scoring: {e}')
                return None

    def validate_preprocessing(self, project_name):
        """
        Check if all preprocessing parameters are set in order to train a model

        :param project_name: The project to check preprocessing parameters for
        :type project_name: str

        :returns: A list of wrong/missing parameters or None
        :rtype: None or list
        """
        _result = None
        for _param_name, _param_type in ProjectManager.__PREPROCESSING_OPTIONS.items():
            if not isinstance(self.get_preprocessing(project_name=project_name, param_name=_param_name), _param_type):
                if _result is None:
                    _result = []
                _result.append(_param_name)
        return _result

    def validate_model_params(self, project_name):
        """
        Check if all model parameters are set in order to train a model

        :param project_name: The project to check model parameters for
        :type project_name: str

        :returns: A list of wrong/missing parameters or None
        :rtype: None or list
        """
        model, _result = self.load_model(project_name), None
        for _param_name, _param_type in ProjectManager.__MODEL_OPTIONS.items():
            if _param_name not in model.keys() or not isinstance(model[_param_name], _param_type):
                if _result is None:
                    _result = []
                _result.append(_param_name)
        return _result

    def validate_training_settings(self, project_name):
        """
        Validate parameters that have not been set

        :param project_name: The project to check parameters for
        :type project_name: str

        :returns: A list of wrong/missing parameters or None
        :rtype: None or list
        """
        _result = None
        for _tmp in [self.validate_preprocessing(project_name), self.validate_model_params(project_name)]:
            if _tmp is not None:
                if _result is None:
                    _result = []
                _result += _tmp
        return _result
