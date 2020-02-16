import logging


class Database:
    def __init__(self, db_instance):
        self.__dbclient = db_instance

    def get_user_projects(self, username):
        """
        Get all projects for a certain user
        """
        try:
            return self.get_all_projects()[username]
        except Exception as e:
            logging.error(f'Something went wrong requesting the projects for user {username}: {e}')
            return []

    def create_project(self, name, description, username):
        """
        Create a new project
        """
        projects = self.get_all_projects()
        if not projects:
            projects = {username: []}

        if username in projects.keys():
            projects[username].append({'name': name, 'description': description})
        else:
            projects[username] = [{'name': name, 'description': description}]
        self.__dbclient.set('projects', projects)

    def get_all_projects(self):
        return self.__dbclient.get('projects')

    def get_project(self, name, username):
        """
        Request data for a single project
        """
        projects = self.get_all_projects()[username]
        for p in projects:
            if p['name'] == name:
                return p

    def drop_project(self, name, username):
        """
        Remove 1 specific project
        """
        projects = self.get_all_projects()
        project_to_trash = self.get_project(name, username)
        projects[username].remove(project_to_trash)
        self.__dbclient.set('projects', projects)

    def does_project_exist(self, projectname, username):
        """
        Check if a project exists or not
        """
        projects = self.get_user_projects(username)
        for p in projects:
            if projectname == p['name']:
                return 1
        return 0
