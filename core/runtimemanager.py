from core.projectruntime import ProjectRuntime
import logging
import gc


class RuntimeManager:
    def __init__(self, project_manager, dataset_dir):
        self.__runtime = {}
        self.__project_manager = project_manager
        self.__dataset_dir = dataset_dir

    def run_project(self, project_name, username):
        """
        Register a project to the runtime
        :param project_name: The project to pop from runtime
        :type project_name: str

        :param username: The username that is running the project
        :type username: str
        """
        self.__runtime[username] = {
            project_name: ProjectRuntime(project_name, self.__project_manager, self.__dataset_dir)}

    def stop_project(self, project_name, username):
        """
        Delete a project from the project runtime
        :param project_name: The project to pop from runtime
        :type project_name: str

        :param username: The username that is running the project
        :type username: str
        """
        self.__runtime[username].pop(project_name)
        gc.collect()

    def is_project_running(self, project_name, username):
        """
        Check if a project is running or not
        :param project_name: The project to pop from runtime
        :type project_name: str

        :param username: The username that is running the project
        :type username: str
        :rtype: bool
        """
        for name, projects in self.__runtime.items():
            if name == username and project_name in projects:
                return 1
        return 0

    def get_data_head(self, project_name, username):
        """
        Return the head(5) from a dataset as HTML

        :param project_name: The project to pop from runtime
        :type project_name: str

        :param username: The username that is running the project
        :type username: str

        :rtype: str or None
        """
        try:
            return self.__runtime[username][project_name].dataset.head().to_html(
                classes='table table-striped table-hover table-scroll text-center',
                border=0,
                notebook=False)
        except Exception as e:
            logging.error(f'Error loading dataset for {e}')
            return None

    def get_column_names(self, project_name, username):
        """
        Retrieve all column names as a list

        :param project_name: The project to pop from runtime
        :type project_name: str

        :param username: The username that is running the project
        :type username: str

        :returns: all column names as a list
        :rtype: list
        """
        try:
            return self.__runtime[username][project_name].dataset.columns.to_list()
        except Exception as e:
            logging.error(f'Error loading column names for project {project_name}: {e}')
            return None

    def rename_column(self, project_name, username, old_col_name, new_col_name):
        """
        Change the name of a column in a DataFrame

        :param project_name: The project to pop from runtime
        :type project_name: str

        :param username: The username that is running the project
        :type username: str

        :param old_col_name: The column to rename
        :type old_col_name: str

        :param new_col_name: The new column name
        :type new_col_name: str

        :returns: Nothing
        """
        try:
            if old_col_name in self.get_column_names(project_name, username) and old_col_name != new_col_name:
                self.__runtime[username][project_name].rename_column(old_col_name, new_col_name)
            else:
                raise ValueError(f'No such column "{old_col_name}" in project {project_name}')
        except Exception as e:
            logging.error(f'Error renaming column: {e}')

    def drop_column(self, project_name, username, col_name):
        """
        Remove a column

        :param project_name: The project to pop from runtime
        :type project_name: str

        :param username: The username that is running the project
        :type username: str

        :param col_name: The column to drop
        :type col_name: str
        """
        try:
            if col_name in self.get_column_names(project_name, username):
                self.__runtime[username][project_name].drop_column(col_name)
            else:
                raise ValueError(f'No such column name: {col_name}')
        except Exception as e:
            logging.error(f'Could not drop column {col_name} from {project_name}: {e}')
