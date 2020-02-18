import logging


class Projects:
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

        if not self.does_project_exist(name, username):
            if username in projects.keys():
                projects[username].append({'name': name, 'description': description})
            else:
                projects[username] = [{'name': name, 'description': description}]
            self.__dbclient.set('projects', projects)

    def get_all_projects(self):
        """
        Request all projects of every user
        """
        return self.__dbclient.get('projects')

    def get_project(self, name, username):
        """
        Request data for a single project
        """
        projects = self.get_all_projects()[username]
        for project in projects:
            if project['name'] == name:
                return project
        return 0

    def drop_project(self, name, username):
        """
        Remove 1 specific project
        """
        projects = self.get_all_projects()
        project_to_trash = self.get_project(name, username)
        projects[username].remove(project_to_trash)
        self.__dbclient.set('projects', projects)

    def update_project(self, oldname, newname, description, username):
        """
        Change the name and/or description of a project if possible
        """
        user_projects = self.get_user_projects(username)
        if self.does_project_exist(newname, username):
            return oldname
        for project in user_projects:
            if project['name'] == oldname:
                user_projects[user_projects.index(project)] = {'name': newname, 'description': description}
        projects = self.get_all_projects()
        projects[username] = user_projects
        self.__dbclient.set('projects', projects)
        return newname

    def does_project_exist(self, projectname, username):
        """
        Check if a project exists or not
        """
        p = self.get_project(projectname, username)
        if p is not 0:
            return 1
        return 0

    def assign_dataset(self, name, projectname, username):
        ...
