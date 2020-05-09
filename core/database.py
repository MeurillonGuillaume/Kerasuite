from pickledb import PickleDB
import logging


class Database(PickleDB):
    def __init__(self, location, sig=True):
        """
        Initialise the superclass PickleDB

        This class inherits all functionality from PickleDB, but has the addition to temporarily duplicate
        data to avoid database corruption. The database instance that is used for user-interaction does not
        write to disk automatically, only the back-up database does this. If an action fails on the primary database,
        it is reverted to the back-up database.

        :param location
        :type location: str

        :param sig: Wether or not to enable the Sigterm handler
        :type sig: bool
        """
        super(Database, self).__init__(
            location=location,
            auto_dump=False,
            sig=sig
        )

        self.__db_duplicate = super(Database, self).__init__(
            location=location,
            auto_dump=True,
            sig=sig
        )

    def __set_duplicate(self, key, value):
        """
        Persist values to the database duplicate

        :param key: Which key to define
        :type key: str or int

        :param value: The value to set for the given key
        """
        self.__db_duplicate.set(
            key=key,
            value=value
        )
        # Write to disk
        self.__db_duplicate.dump()

    def set(self, key, value):
        """
        Attempt to set the value of a key in the primary and duplicate database

        :param key: Which key to define
        :type key: str or int

        :param value: The value to set for the given key
        """
        try:
            if super(Database, self).set(key=key, value=value):
                self.__set_duplicate(
                    key=key,
                    value=value
                )
                return True
        except Exception as e:
            logging.error(f'There was an error setting ({key}:{value}) to the database: {e}')
