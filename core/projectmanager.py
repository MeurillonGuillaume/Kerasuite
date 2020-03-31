import logging
from os import remove
import pathlib


class ProjectManager:
    def __init__(self, db_instance):
        self.__dbclient = db_instance

    def get_user_projects(self, username):
        """
        Get all projects for a certain user

        :param username: The username to return project from
        :type username: str

        :returns: a list of projects, or an empty list if no projects are available
        :rtype: list
        """
        try:
            return self.get_all_projects()[username]
        except Exception as e:
            logging.error(f'Something went wrong requesting the projects for user {username}: {e}')
            return []

    def create_project(self, name, description, username):
        """
        Create a new project for a certain user

        :param name: The name to give to this project
        :type name: str

        :param description: A description about the project
        :type description: str

        :param username: The user to register this project for
        :type username: str
        """
        projects = self.get_all_projects()
        if not projects:
            projects = {}

        if username not in projects:
            projects[username] = []

        if not self.does_project_exist(name, username):
            if username in projects.keys():
                projects[username].append({'name': name, 'description': description})
            else:
                projects[username] = [{'name': name, 'description': description}]
            self.__dbclient.set('projects', projects)
            self.__dbclient.dump()

    def get_all_projects(self):
        """
        Request all projects of every user

        :rtype: dict
        """
        return self.__dbclient.get('projects')

    def get_project(self, name, username):
        """
        Request data for a single project

        :param name: The name of the project to retrieve
        :type name: str

        :param username: The user that owns this project
        :type username: str

        :rtype: dict
        """
        projects = self.get_all_projects()
        if not isinstance(projects, bool):
            projects = projects[username]
            for project in projects:
                if project['name'] == name:
                    return project
        return 0

    def drop_project(self, name, username):
        """
        Remove 1 specific project

        :param name: The name of the project to delete
        :type name: str

        :param username: The user that owns this project
        :type username: str
        """
        projects = self.get_all_projects()
        project_to_trash = self.get_project(name, username)
        projects[username].remove(project_to_trash)
        self.__dbclient.set('projects', projects)
        self.__dbclient.dump()

    def update_project(self, oldname, newname, description, username):
        """
        Change the name and/or description of a project if possible

        :param oldname: The current project name
        :type oldname: str

        :param newname: The new name to assign to this project
        :type newname: str

        :param description: An optional updated description for the project
        :type description: str

        :param username: The user that owns this project
        :type username: str
        """
        user_projects = self.get_user_projects(username)
        if self.does_project_exist(newname, username):
            if oldname != newname:
                return oldname
        # Change settings for the general project
        for project in user_projects:
            if project['name'] == oldname:
                user_projects[user_projects.index(project)] = {'name': newname, 'description': description}
                # Change the name in the database under project datasets as well
                if self.does_project_have_dataset(oldname, username):
                    self.reassign_dataset(oldname, newname, username)

        projects = self.get_all_projects()
        projects[username] = user_projects
        self.__dbclient.set('projects', projects)
        self.__dbclient.dump()
        return newname

    def does_project_exist(self, projectname, username):
        """
        Check if a project exists or not

        :param projectname: The project to check existence of
        :type projectname: str

        :param username: The user to check
        :type username: str

        :rtype: bool
        """
        p = self.get_project(projectname, username)
        if p is not 0:
            return 1
        return 0

    def get_all_datasets(self):
        """
        Retrieve all datasets

        :rtype: dict
        """
        return self.__dbclient.get('datasets')

    def assign_dataset(self, name, data_type, projectname, username):
        """
        Assign a dataset to a users project

        :param name: The name of the dataset, an UUID4
        :type name: str

        :param data_type: The type of dataset, currently only JSON and CSV
        :type data_type: str

        :param projectname: The name of the project
        :type projectname: str

        :param username: The user that owns the project
        :type username: str
        """
        data = self.get_all_datasets()
        if not data:
            data = {username: []}

        i = 0
        for project in data[username]:
            if project['projectname'] == projectname:
                data[username][i]['dataset'] = name
                data[username][i]['datatype'] = data_type
                self.__dbclient.set('datasets', data)
                self.__dbclient.dump()
                return 1
            i += 1
        data[username].append({'projectname': projectname, 'datatype': data_type, 'dataset': name})
        self.__dbclient.set('datasets', data)

    def reassign_dataset(self, old_name, new_name, username):
        """
        Move the dataset from one project to another, used when renaming a project

        :param old_name: Current projectname the dataset is assigned to
        :type old_name: str

        :param new_name: New projectname to assign the dataset to
        :type new_name: str

        :param username: The user that owns it
        :type username: str
        """
        data = self.get_all_datasets()
        for i in range(len(data[username])):
            if data[username][i]['projectname'] == old_name:
                data[username][i]['projectname'] = new_name
        self.__dbclient.set('datasets', data)
        self.__dbclient.dump()

    def does_project_have_dataset(self, projectname, username):
        """
        Check if a project does have a dataset assigned

        :param projectname: The project to check
        :type projectname: str

        :param username: The owner of the project
        :type username: str
        """
        data = self.get_all_datasets()
        if data:
            if username in data.keys():
                for project in data[username]:
                    if project['projectname'] == projectname:
                        if project['dataset'] is not None and project['datatype'] is not None:
                            return 1
        return 0

    def get_project_dataset(self, projectname, username):
        """
        Get the name of the dataset

        :param projectname: The project to retrieve
        :type projectname: str

        :param username: The owner of the project
        :type username: str
        """
        data = self.get_all_datasets()
        if data:
            if username in data.keys():
                for project in data[username]:
                    if project['projectname'] == projectname:
                        return f'{project["dataset"]}.{project["datatype"]}'
        return None

    def clear_project_dataset(self, projectname, username):
        """
        Delete the dataset from a project

        :param projectname: The project to delete
        :type projectname: str

        :param username: The owner of the project
        :type username: str
        """
        data = self.get_all_datasets()
        if data:
            for i in range(len(data[username])):
                if data[username][i]['projectname'] == projectname:
                    dataset = self.get_project_dataset(projectname, username)
                    remove(f'{pathlib.Path(__file__).parent.parent.absolute()}/data/{dataset}')
                    data[username].remove(data[username][i])
                    self.__dbclient.set('datasets', data)
                    self.__dbclient.dump()
