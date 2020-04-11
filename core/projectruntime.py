import logging
import pandas as pd
from flask import session
from core.projectmanager import ProjectManager


class ProjectRuntime:
    def __init__(self, project_name, project_manager, dataset_dir):
        """
        Initialise project runtime

        :param project_name:
        :type project_name: str

        :param project_manager:
        :type project_manager: ProjectManager

        :param dataset_dir:
        :type dataset_dir: str
        """
        self.dataset = None
        self.__project_name = project_name
        self.dataset_name = project_manager.get_project_dataset(self.__project_name, session['username'])
        self.__dataset_dir = dataset_dir
        self.__load_dataset()

    def __load_dataset(self):
        """
        Load a dataset into memory
        """
        try:
            if '.csv' in self.dataset_name:
                self.dataset = pd.read_csv(f'{self.__dataset_dir}/{self.dataset_name}')
            elif 'json' in self.dataset_name:
                self.dataset = pd.read_json(f'{self.__dataset_dir}/{self.dataset_name}')
        except Exception as e:
            logging.error(f'The dataset contains invalid encoding! {e}')
            self.dataset = None

    def __write_dataset_to_disk(self):
        """
        Store data to disk after a change

        :returns: Nothing
        :rtype: None
        """
        try:
            if '.csv' in self.dataset_name:
                self.dataset.to_csv(f'{self.__dataset_dir}/{self.dataset_name}',
                                    index=False)
            elif '.json' in self.dataset_name:
                self.dataset.to_json(f'{self.__dataset_dir}/{self.dataset_name}',
                                     orient='records')
            logging.info(f'Written dataset {self.dataset_name} to disk for project {self.__project_name}')
        except Exception as e:
            logging.error(f'Error writing dataset for project {self.__project_name} to disk: {e}')

    def get_dataset_head(self):
        """
        Return the head of the dataset as a HTML table
        """
        return self.dataset.head().to_html(
            classes='table table-striped table-hover table-scroll text-center',
            border=0,
            notebook=False)

    def rename_column(self, old_name, new_name):
        """
        Rename a column

        :param old_name: The current column name
        :type old_name: str

        :param new_name: The new column name
        :type new_name: str

        :returns: Nothing
        :rtype: None
        """
        self.dataset = self.dataset.rename(columns={
            old_name: new_name
        })
        self.__write_dataset_to_disk()

    def drop_column(self, col_name):
        """
        Remove a column from the current dataset

        :param col_name: The column to drop
        :type col_name: str

        :returns: Nothing
        :rtype: None
        """
        self.dataset = self.dataset.drop([col_name], axis=1)
        self.__write_dataset_to_disk()
