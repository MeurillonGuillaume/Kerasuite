import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, Normalizer, \
    QuantileTransformer, PowerTransformer
from core.modelmanager import ModelManager
from core.projectmanager import ProjectManager


class ProjectRuntime:
    def __init__(self, project_name, project_manager, dataset_dir):
        """
        Initialise project runtime

        :param project_name: The name of the current project which is running
        :type project_name: str

        :param project_manager: A pointer to the manager with database access
        :type project_manager: ProjectManager

        :param dataset_dir: The directory where datasets can be found
        :type dataset_dir: str
        """
        self.dataset = None
        self.__project_name = project_name
        self.dataset_name = project_manager.get_project_dataset(self.__project_name)
        self.__project_manager = project_manager
        self.__dataset_dir = dataset_dir
        self.__load_dataset()
        self.model_manager = ModelManager(project_name, project_manager)
        self.__x_train, self.__x_test, self.__y_train, self.__y_test = None, None, None, None

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

        :rtype: str
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

    def get_columns(self):
        """
        Load all columns as a list

        :returns: A list of column names
        :rtype: list
        """
        return self.dataset.columns.to_list()

    def replace_values(self, column, old_value, new_value):
        """
        Replace specific values in a column with a new value

        :param column: The column in which values are to be changed
        :type column: str

        :param old_value: The value in the column to replace
        :type old_value: str

        :param new_value: The new value to put in the column
        :type new_value: str
        """
        self.dataset[column] = self.dataset[column].replace(old_value, new_value)
        self.__write_dataset_to_disk()

    def preprocess_dataset(self, columns, method):
        """
        Preprocess columns

        :param columns: The columns to preprocess
        :type columns: list

        :param method: Which method of preprocessing to use, see RuntimeManager
        :type method: str
        """
        logging.info(f'Preprocessing {columns} with {method}')

        # Handle the preprocessing method
        if method == 'StandardScaler':
            scale_method = StandardScaler()
        elif method == 'MaxAbsScaler':
            scale_method = MaxAbsScaler()
        elif method == 'RobustScaler':
            scale_method = RobustScaler()
        elif method == 'Min-Max Scaler':
            scale_method = MinMaxScaler()
        elif method == 'Normalizer':
            scale_method = Normalizer()
        elif method == 'QuantileTransformer':
            scale_method = QuantileTransformer()
        elif method == 'PowerTransformer':
            scale_method = PowerTransformer()
        else:
            raise ValueError(f'Preprocessing {method} does not exist!')

        # Process data
        self.dataset[columns] = scale_method.fit_transform(self.dataset[columns])
        # Write to disk
        self.__write_dataset_to_disk()

    def get_data_balance(self):
        """
        Get the count for each unique value in each column

        :rtype: dict
        :returns: a dictionary with all unique values per column name and their value counts
        """
        results = {}
        if self.dataset is not None:
            for column in self.dataset.columns.to_list():
                results[column] = self.dataset[column].value_counts().to_dict()
        return results

    def train_test_split(self):
        """
        Split the dataset in train- and test-data

        :rtype: bool
        """
        # Request parameters
        _split_size = self.__project_manager.get_preprocessing(self.__project_name, 'train-test-split') / 100.0
        _random_state = self.__project_manager.get_preprocessing(self.__project_name, 'random-state')
        _output_cols = self.__project_manager.get_preprocessing(self.__project_name, 'output-columns')

        # Check if parameters have been set
        if _split_size is not None and _random_state is not None and _output_cols is not None:
            # Load features
            _x = self.dataset.drop(_output_cols, axis=1)
            # Load targets
            _y = self.dataset[_output_cols]
            # Split features & according targets to train- and test-sets according to random-state and split-size
            self.__x_train, self.__x_test, self.__y_train, self.__y_test = train_test_split(_x, _y,
                                                                                            random_state=_random_state,
                                                                                            train_size=_split_size)
            return 1
        return 0

    def train_model(self):
        """
        Attempt training the model for the current running project
        """
        self.__project_manager.store_model_scoring(
            project_name=self.__project_name,
            scoring=self.model_manager.train_model(
                x_train=self.__x_train,
                y_train=self.__y_train
            ),
            scoring_source='train'
        )

    def test_model(self):
        """
        Attempt evaluating the model that has been trained for the current project
        """
        self.__project_manager.store_model_scoring(
            project_name=self.__project_name,
            scoring=self.model_manager.test_model(
                x_test=self.__x_test,
                y_test=self.__y_test
            )
        )
