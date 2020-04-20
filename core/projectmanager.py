import logging
import time
from os import remove
import pathlib
from flask import session
from uuid import uuid4


class ProjectManager:
    def __init__(self, db_instance):
        self.__dbclient = db_instance

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
            self.__dbclient.set('projects', projects)
            self.__dbclient.dump()

    def get_all_projects(self):
        """
        Request all projects of every user

        :rtype: dict
        """
        return self.__dbclient.get('projects')

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
        self.__dbclient.set('projects', projects)
        self.__dbclient.dump()
        # Remove dataset from database entry
        self.clear_project_dataset(project_to_trash['name'])

    def update_project(self, oldname, newname, description):
        """
        Change the name and/or description of a project if possible

        :param oldname: The current project name
        :type oldname: str

        :param newname: The new name to assign to this project
        :type newname: str

        :param description: An optional updated description for the project
        :type description: str
        """
        user_projects = self.get_user_projects()
        if self.does_project_exist(newname):
            if oldname != newname:
                return oldname
        # Change settings for the general project
        for project in user_projects:
            if project['name'] == oldname:
                user_projects[user_projects.index(project)] = {'name': newname, 'description': description}
                # Change the name in the database under project datasets as well
                if self.does_project_have_dataset(oldname):
                    self.reassign_dataset(oldname, newname)

        projects = self.get_all_projects()
        projects[session['username']] = user_projects
        self.__dbclient.set('projects', projects)
        self.__dbclient.dump()
        return newname

    def does_project_exist(self, projectname):
        """
        Check if a project exists or not

        :param projectname: The project to check existence of
        :type projectname: str

        :rtype: bool
        """
        p = self.get_project(projectname)
        if p is not 0:
            return 1
        return 0

    def get_all_datasets(self):
        """
        Retrieve all datasets

        :rtype: dict
        """
        return self.__dbclient.get('datasets')

    def assign_dataset(self, name, data_type, projectname):
        """
        Assign a dataset to a users project

        :param name: The name of the dataset, an UUID4
        :type name: str

        :param data_type: The type of dataset, currently only JSON and CSV
        :type data_type: str

        :param projectname: The name of the project
        :type projectname: str
        """
        data = self.get_all_datasets()
        if not data:
            data = {session['username']: []}

        i = 0
        for project in data[session['username']]:
            if project['projectname'] == projectname:
                data[session['username']][i] = {
                    'dataset': name,
                    'datatype': data_type,
                    'preprocessing': {
                        'train-test-split': 70,
                        'random_state': 0,
                        'output-columns': []
                    }
                }
                self.__dbclient.set('datasets', data)
                self.__dbclient.dump()
                return 1
            i += 1
        data[session['username']].append({
            'projectname': projectname,
            'datatype': data_type,
            'dataset': name,
            'preprocessing': {
                'train-test-split': 70,
                'random_state': 0,
                'output-columns': []
            }
        })
        self.__dbclient.set('datasets', data)

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
        self.__dbclient.set('datasets', data)
        self.__dbclient.dump()

    def does_project_have_dataset(self, projectname):
        """
        Check if a project does have a dataset assigned

        :param projectname: The project to check
        :type projectname: str
        """
        data = self.get_all_datasets()
        if data:
            if session['username'] in data.keys():
                for project in data[session['username']]:
                    if project['projectname'] == projectname:
                        if project['dataset'] is not None and project['datatype'] is not None:
                            return 1
        return 0

    def get_project_dataset(self, projectname):
        """
        Get the name of the dataset

        :param projectname: The project to retrieve
        :type projectname: str
        """
        data = self.get_all_datasets()
        if data:
            if session['username'] in data.keys():
                for project in data[session['username']]:
                    if project['projectname'] == projectname:
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
                    self.__dbclient.set('datasets', data)
                    self.__dbclient.dump()

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
                    _project['preprocessing'][param] = value
                    self.__dbclient.set('datasets', data)
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
        """
        try:
            return self.__dbclient.get('models')
        except Exception as e:
            logging.error(f'Error loading models: {e}')

    def create_model(self, project_name):
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
                'batch-size': 1,
                'layers': [],
                'timestamp': time.time(),
                'validation-split': 0.75
            }
            # TODO: handle creating a new model
        self.__dbclient.set('models', models)

    def add_model_layer(self, project_name, layer_type):
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
            'order': layer_number
        })
        self.__dbclient.set('models', models)

    def load_model(self, project_name):
        models = self.get_all_models()
        if not models or session['username'] not in models or project_name not in models[session['username']]:
            return None
        else:
            return models[session['username']][project_name]
