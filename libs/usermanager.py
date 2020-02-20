from passlib.hash import bcrypt
import logging


class UserManager:
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
            logging.info(f'Attempting to login with username "{username}" and password "{password}"')
            userdata = self.__dbclient.get('users')[username]['password']
            if userdata is not None:
                # Will return True if the submitted password matches the hashed password
                return bcrypt.verify(password, userdata)
            return 0
        except Exception as e:
            logging.error(f'Failed attempt at logging in with username "{username}" and password "{password}": {e}')
            return 0
