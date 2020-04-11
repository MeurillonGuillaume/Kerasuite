import pandas as pd
from flask import session
import logging


class ProjectRuntime:
    def __init__(self, project_name, project_manager, dataset_dir):
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
        """
        self.dataset = self.dataset.rename(columns={
            old_name: new_name
        })

    def drop_column(self, col_name):
        """
        Remove a column from the current dataset

        :param col_name: The column to drop
        :type col_name: str
        """
        self.dataset = self.dataset.drop([col_name], axis=1)
