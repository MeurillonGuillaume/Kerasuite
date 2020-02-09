import json
import logging
import os


class Secrets:
    def __init__(self, store_path):
        """
        Attempt to load the file where all secrets are stored
        :param store_path: String: path tho where the secrets file is stored
        """
        if os.path.exists(store_path):
            logging.info(f'Loading secrets file "{store_path}"')
            self.__storage = json.load(open(store_path))
        else:
            logging.warning(f'The secrets file "{store_path}" does not exist! Creating empty secrets file.')

    def get_user(self, username):
        """
        Retrieve user information
        :param username: String: username to retrieve data from
        """
        try:
            logging.info(f'Requesting password for user "{username}"')
            return self.__storage['users'][username]
        except Exception as e:
            logging.error(f'There is no user "{username}": {e}')
            return None
