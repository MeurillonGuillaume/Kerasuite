from passlib.hash import bcrypt
import logging
from re import match


class UserManager:
    @staticmethod
    def is_password_strong(password):
        """
        Check if a password matches the front-end validation
        """
        if match('(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$', password):
            return 1
        return 0

    def __init__(self, db):
        self.__dbclient = db

    def attempt_login(self, username, password):
        """
        Attempt to login a user
        :param username: String: The username to attempt logging in
        :param password: String: The password, unhashed, received from user input
        :return: Boolean: True or False
        """
        try:
            logging.info(f'Attempting to login with username "{username}" and password "{bcrypt.hash(password)}"')
            userdata = self.__dbclient.get('users')[username]['password']
            if userdata is not None:
                # Will return True if the submitted password matches the hashed password
                return bcrypt.verify(password, userdata)
            return 0
        except Exception as e:
            logging.error(
                f'Failed attempt at logging in with username "{username}" and password "{bcrypt.hash(password)}": {e}')
            return 0

    def has_elevated_rights(self, username):
        """
        Check if a user has elevated rights or not
        """
        try:
            return self.__dbclient.get('users')[username]["admin"]
        except Exception as e:
            logging.error(f'Error retrieving user rights: {e}')
            return 0

    def get_users(self, username):
        """
        Get all users
        """
        if self.has_elevated_rights(username):
            return self.__dbclient.get('users')
        return None

    def does_user_exist(self, username):
        """
        Check if a user actually exists
        """
        users = self.__dbclient.get('users')
        if username in users.keys():
            return 1
        return 0

    def delete_user(self, username):
        """
        Delete a user from the database
        """
        users = self.__dbclient.get('users')
        del users[username]
        self.__dbclient.set('users', users)

    def register_user(self, username, password, elevated_rights):
        """
        Create a new user
        """
        users = self.__dbclient.get('users')
        users[username] = {"password": bcrypt.hash(password), "admin": elevated_rights}
        self.__dbclient.set('users', users)

    def change_permissions(self, username):
        """
        Swap the permissions assigned to a user
        """
        users = self.__dbclient.get('users')
        users[username]['admin'] = not users[username]['admin']
        self.__dbclient.set('users', users)

    def admin_has_default_pass(self):
        """
        Check if the admin has changed his password
        """
        return bcrypt.verify('Kerasuite', self.__dbclient.get('users')['admin']['password'])

    def change_password(self, old, new, new_repeat, username):
        """
        Change the current users password
        """
        if new == new_repeat:
            if self.attempt_login(username, old):
                users = self.__dbclient.get('users')
                users[username]['password'] = bcrypt.hash(new)
                self.__dbclient.set('users', users)
