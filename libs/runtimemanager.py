from libs.projectruntime import ProjectRuntime
import logging
import json


class RuntimeManager:
    def __init__(self, project_manager, dataset_dir):
        self.__runtime = {}
        self.__project_manager = project_manager
        self.__dataset_dir = dataset_dir

    def run_project(self, project_name, username):
        """
        Register a project to the runtime
        :type project_name: str
       p :type username: str
        :rtype: None
        """
        self.__runtime[username] = {
            project_name: ProjectRuntime(project_name, self.__project_manager, self.__dataset_dir)}

    def is_project_running(self, project_name, username):
        """
        Check if a project is running or not
        :type project_name: str
        :type username: str
        :rtype: bool
        """
        for name, project in self.__runtime.items():
            if name == username and project == project_name:
                return 1
        return 0

    def get_data_head(self, project_name, username):
        try:
            return self.__runtime[username][project_name].dataset.head().to_html(
                classes='table table-striped table-hover table-scroll',
                border=0,
                notebook=False)
        except Exception as e:
            logging.error(e)
            return None
