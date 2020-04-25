import logging
from re import match
from pickledb import PickleDB
from flask import session
from passlib.hash import bcrypt


class UserManager:
    @staticmethod
    def is_password_strong(password):
        """
        Check if a password matches the front-end validation

        :param password: A password String to check
        :type password: str

        :rtype: bool
        :returns: True or False
        """
        if match(r'(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$', password):
            return 1
        return 0

    def __init__(self, db):
        """
        Create an usermanager instance

        :param db:
        :type db: PickleDB
        """
        self.__dbclient = db

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
            userdata = self.__dbclient.get('users')[username]['password']
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
            return self.__dbclient.get('users')[session['username']]["admin"]
        except Exception as e:
            logging.error(f'Error retrieving user rights: {e}')
            return 0

    def get_users(self):
        """
        Get all users

        :rtype: dict
        """
        if self.has_elevated_rights():
            return self.__dbclient.get('users')
        return None

    def does_user_exist(self, username):
        """
        Check if a user actually exists

        :param username: An username to check
        :type username: str

        :rtype: bool
        """
        users = self.__dbclient.get('users')
        if username in users.keys():
            return 1
        return 0

    def delete_user(self, username):
        """
        Delete a user from the database

        :param username: An username to delete
        :type username: str
        """
        users = self.__dbclient.get('users')
        del users[username]
        self.__dbclient.set('users', users)
        self.__dbclient.dump()

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
        users = self.__dbclient.get('users')
        users[username] = {"password": bcrypt.hash(password), "admin": elevated_rights}
        self.__dbclient.set('users', users)
        self.__dbclient.dump()

    def change_permissions(self, username):
        """
        Swap the permissions assigned to a user

        :param username: An username to change permissions for
        :type username: str
        """
        users = self.__dbclient.get('users')
        users[username]['admin'] = not users[username]['admin']
        self.__dbclient.set('users', users)
        self.__dbclient.dump()

    def admin_has_default_pass(self):
        """
        Check if the admin has changed his password
        :rtype: bool
        """
        return bcrypt.verify('Kerasuite', self.__dbclient.get('users')['admin']['password'])

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
                users = self.__dbclient.get('users')
                users[session['username']]['password'] = bcrypt.hash(new)
                self.__dbclient.set('users', users)
                self.__dbclient.dump()
