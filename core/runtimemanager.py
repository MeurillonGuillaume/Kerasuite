import gc
import logging

from flask import session

from core.projectmanager import ProjectManager
from core.projectruntime import ProjectRuntime


class RuntimeManager:
    def __init__(self, project_manager, dataset_dir):
        """
        Manager class to keep track of all projects in the runtime

        :param project_manager: A pointer to the manager with database access
        :type project_manager: ProjectManager

        :param dataset_dir: The directory where data sets can be found
        :type dataset_dir: str
        """
        self.__runtime = {}
        self.__project_manager = project_manager
        self.__dataset_dir = dataset_dir

    def run_project(self, project_name):
        """
        Register a project to the runtime

        :param project_name: The project to pop from runtime
        :type project_name: str
        """
        if session['username'] in self.__runtime:
            self.__runtime[session['username']][project_name] = ProjectRuntime(project_name,
                                                                               self.__project_manager,
                                                                               self.__dataset_dir)
        else:
            self.__runtime[session['username']] = {
                project_name: ProjectRuntime(project_name,
                                             self.__project_manager,
                                             self.__dataset_dir)
            }

    def stop_project(self, project_name):
        """
        Delete a project from the project runtime

        :param project_name: The project to pop from runtime
        :type project_name: str
        """
        self.__runtime[session['username']].pop(project_name)
        gc.collect()

    def is_project_running(self, project_name):
        """
        Check if a project is running or not

        :param project_name: The project to pop from runtime
        :type project_name: str

        :returns: A boolean representing the project running state
        :rtype: bool
        """
        for name, projects in self.__runtime.items():
            if name == session['username'] and project_name in projects:
                return 1
        return 0

    def get_data_head(self, project_name):
        """
        Return the head(5) from a dataset as HTML

        :param project_name: The project to pop from runtime
        :type project_name: str

        :rtype: str or None
        """
        try:
            return self.__runtime[session['username']][project_name].dataset.head().to_html(
                classes='table table-striped table-hover table-scroll text-center',
                border=0,
                notebook=False)
        except Exception as e:
            logging.error(f'Error loading dataset for {e}')
            return None

    def get_column_names(self, project_name):
        """
        Retrieve all column names as a list

        :param project_name: The project to pop from runtime
        :type project_name: str

        :returns: all column names as a list
        :rtype: list
        """
        try:
            return self.__runtime[session['username']][project_name].get_columns()
        except Exception as e:
            logging.error(f'Error loading column names for project {project_name}: {e}')
            return None

    def rename_column(self, project_name, old_col_name, new_col_name):
        """
        Change the name of a column in a DataFrame

        :param project_name: The project to pop from runtime
        :type project_name: str

        :param old_col_name: The column to rename
        :type old_col_name: str

        :param new_col_name: The new column name
        :type new_col_name: str

        :returns: Nothing
        """
        try:
            if old_col_name in self.get_column_names(project_name) and old_col_name != new_col_name:
                self.__runtime[session['username']][project_name].rename_column(old_name=old_col_name,
                                                                                new_name=new_col_name)
            else:
                raise ValueError(f'No such column "{old_col_name}" in project {project_name}')
        except Exception as e:
            logging.error(f'Error renaming column: {e}')

    def drop_column(self, project_name, col_name):
        """
        Remove a column

        :param project_name: The project to pop from runtime
        :type project_name: str

        :param col_name: The column to drop
        :type col_name: str
        """
        try:
            if col_name in self.get_column_names(project_name):
                self.__runtime[session['username']][project_name].drop_column(col_name=col_name)
            else:
                raise ValueError(f'No such column name: {col_name}')
        except Exception as e:
            logging.error(f'Could not drop column {col_name} from {project_name}: {e}')

    def replace_values(self, project_name, col_name, value_old, value_new):
        """
        Replace the values in a column with new values
        This function passes to the actual executor function in project runtime

        :param project_name: The name of the project in the runtime
        :type project_name: str

        :param col_name: The column in which values are to be changed
        :type col_name: str

        :param value_old: The value in the column to replace
        :type value_old: str

        :param value_new: The new value to put in the column
        :type value_new: str
        """
        try:
            if col_name in self.get_column_names(project_name):
                self.__runtime[session['username']][project_name].replace_values(column=col_name,
                                                                                 old_value=value_old,
                                                                                 new_value=value_new)
            else:
                raise ValueError(f'No such column name: {col_name}')
        except Exception as e:
            logging.error(
                f'Could not replace values ({value_old} -> {value_new}) in project {project_name} for column {col_name}: {e}')

    def preprocess_project(self, project_name, method, columns):
        """
        Pass preprocessing to the project runtime

        :param project_name: The name of the project in the runtime
        :type project_name: str

        :param method: The method to use to process the data
        :type method: str

        :param columns: The columns to preprocess
        :type columns: list
        """
        try:
            self.__runtime[session['username']][project_name].preprocess_dataset(method=method,
                                                                                 columns=columns)
        except Exception as e:
            logging.error(
                f'Could not preprocess the columns {columns} with method {method} in project {project_name}: {e}')

    def get_data_balance(self, project_name):
        """
        Return the balancing of a dataset

        :param project_name: The project to request data balance from
        :type project_name: str

        :rtype: dict
        """
        try:
            return self.__runtime[session['username']][project_name].get_data_balance()
        except Exception as e:
            logging.error(e)

    def get_running_projects(self):
        """
        Retrieve a list of currently running projects for a user

        :rtype: list
        """
        try:
            if session['username'] in self.__runtime:
                return list(self.__runtime[session['username']].keys())
            return []
        except Exception as e:
            logging.error(f'Error loading active projects for {session["username"]}: {e}')
            return []

    def split_project_dataset(self, project_name):
        """
        Split the dataset in a train- and testset for a certain project

        :param project_name: The project to split the dataset for
        :type project_name: str
        """
        self.__runtime[session['username']][project_name].train_test_split()

    def train_project_model(self, project_name):
        """
        Train the model

        :param project_name: The project to train a model for
        :type project_name: str
        """
        self.split_project_dataset(project_name=project_name)
        self.__runtime[session['username']][project_name].train_model()
        self.__runtime[session['username']][project_name].test_model()

    def get_dataset_length(self, project_name):
        """
        Get the length of the dataset

        :param project_name: The project to get the dataset length for
        :type project_name: str
        """
        return self.__runtime[session['username']][project_name].get_dataset_length()

    def get_model_param(self, project_name, key):
        """
        Get a specific model parameter

        :param project_name: The project to get the dataset length for
        :type project_name: str

        :param key: the name of the parameter to request
        :type key: str
        """
        return self.__runtime[session['username']][project_name].get_model_param(key)
