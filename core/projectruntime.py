import pandas as pd
from flask import session
import logging


class ProjectRuntime:
    def __init__(self, project_name, project_manager, dataset_dir):
        self.__project_name = project_name
        self.dataset_name = project_manager.get_project_dataset(self.__project_name, session['username'])
        self.__dataset_dir = dataset_dir
        self.__load_dataset()

    def __load_dataset(self):
        try:
            if '.csv' in self.dataset_name:
                self.dataset = pd.read_csv(f'{self.__dataset_dir}/{self.dataset_name}')
            elif 'json' in self.dataset_name:
                self.dataset = pd.read_json(f'{self.__dataset_dir}/{self.dataset_name}')
        except Exception as e:
            logging.error(f'The dataset contains invalid encoding! {e}')
            self.dataset = None
