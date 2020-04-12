from core.projectruntime import ProjectRuntime
import logging
from flask import session
import gc


class RuntimeManager:
    def __init__(self, project_manager, dataset_dir):
        self.__runtime = {}
        self.__project_manager = project_manager
        self.__dataset_dir = dataset_dir

    def run_project(self, project_name):
        """
        Register a project to the runtime

        :param project_name: The project to pop from runtime
        :type project_name: str
        """
        self.__runtime[session['username']] = {
            project_name: ProjectRuntime(project_name, self.__project_manager, self.__dataset_dir)}

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
                self.__runtime[session['username']][project_name].rename_column(old_col_name, new_col_name)
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
                self.__runtime[session['username']][project_name].drop_column(col_name)
            else:
                raise ValueError(f'No such column name: {col_name}')
        except Exception as e:
            logging.error(f'Could not drop column {col_name} from {project_name}: {e}')

    def replace_values(self, project_name, col_name, value_old, value_new):
        try:
            if col_name in self.get_column_names(project_name):
                self.__runtime[session['username']][project_name].replace_values(col_name,
                                                                                 value_old,
                                                                                 value_new)
            else:
                raise ValueError(f'No such column name: {col_name}')
        except Exception as e:
            logging.error(
                f'Could not replace values ({value_old} -> {value_new}) in project {project_name} for column {col_name}: {e}')
