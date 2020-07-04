import logging

from flask import session
from passlib.hash import bcrypt
from pickledb import PickleDB


class UserManager:

    def __init__(self, db):
        """
        Create an usermanager instance

        :param db: A pointer to the database connector
        :type db: PickleDB
        """
        self.__db_client = db

    def attempt_login(self, username, password):
        """
        Attempt to login a user

        :param username: The username to attempt logging in
        :type username: str

        :param password: The password, unhashed, received from user input
        :type password: str

        :rtype: bool
        :return: True or False
        """
        try:
            logging.info(f'Attempting to login with username "{username}"')
            userdata = self.__db_client.get('users')[username]['password']
            if userdata is not None:
                # Will return True if the submitted password matches the hashed password
                return bcrypt.verify(password, userdata)
            return 0
        except Exception as e:
            logging.error(
                f'Failed attempt at logging in with username "{username}": {e}')
            return 0

    def has_elevated_rights(self):
        """
        Check if a user has elevated rights or not

        :rtype: bool
        """
        try:
            return self.__db_client.get('users')[session['username']]["admin"]
        except Exception as e:
            logging.error(f'Error retrieving user rights: {e}')
            return 0

    def get_users(self):
        """
        Get all users

        :rtype: dict
        """
        if self.has_elevated_rights():
            return self.__db_client.get('users')
        return None

    def does_user_exist(self, username):
        """
        Check if a user actually exists

        :param username: An username to check
        :type username: str

        :rtype: bool
        """
        users = self.__db_client.get('users')
        if username in users.keys():
            return 1
        return 0

    def delete_user(self, username):
        """
        Delete a user from the database

        :param username: An username to delete
        :type username: str
        """
        users = self.__db_client.get('users')
        del users[username]
        self.__db_client.set('users', users)
        self.__db_client.dump()

    def register_user(self, username, password, elevated_rights):
        """
        Create a new user

        :param username: An username to create
        :type username: str

        :param password: A password to create for the user
        :type password:str

        :param elevated_rights: Does the newly created user have elevated rights or not
        :type elevated_rights: bool
        """
        users = self.__db_client.get('users')
        users[username] = {"password": bcrypt.hash(password), "admin": elevated_rights}
        self.__db_client.set('users', users)
        self.__db_client.dump()

    def change_permissions(self, username):
        """
        Swap the permissions assigned to a user

        :param username: An username to change permissions for
        :type username: str
        """
        users = self.__db_client.get('users')
        users[username]['admin'] = not users[username]['admin']
        self.__db_client.set('users', users)
        self.__db_client.dump()

    def admin_has_default_pass(self):
        """
        Check if the admin has changed his password
        :rtype: bool
        """
        return bcrypt.verify('Kerasuite', self.__db_client.get('users')['admin']['password'])

    def change_password(self, old, new, new_repeat):
        """
        Change the current users password

        :param old: The old password to change
        :type old: str

        :param new: The new password to change to
        :type new: str

        :param new_repeat: Repeat of the new password for typo verification
        :type new_repeat: str
        """
        if new == new_repeat:
            if self.attempt_login(session['username'], old):
                users = self.__db_client.get('users')
                users[session['username']]['password'] = bcrypt.hash(new)
                self.__db_client.set('users', users)
                self.__db_client.dump()
