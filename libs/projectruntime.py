import pandas as pd
from flask import session
from os import path


class ProjectRuntime:
    def __init__(self, project_name, project_manager, dataset_dir):
        self.__project_name = project_name
        self.dataset_name = project_manager.get_project_dataset(self.__project_name, session['username'])
        if '.csv' in self.dataset_name:
            self.dataset = pd.read_csv(f'{dataset_dir}/{self.dataset_name}')
        elif 'json' in self.dataset_name:
            self.dataset = pd.read_json(f'{dataset_dir}/{self.dataset_name}')
