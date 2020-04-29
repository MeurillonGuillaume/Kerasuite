from tensorflow import keras
from pandas import Series
from tensorflow.keras.layers import Dense, Dropout
from core.projectmanager import ProjectManager


class ModelManager:
    @staticmethod
    def __get_input_shape(targets):
        """
        :param targets:
        :type targets: Series
        """
        return targets.shape

    def __init__(self, project_name, project_manager):
        """
        :type project_manager: ProjectManager
        """
        self.__project_manager = project_manager
        self.__project_name = project_name
        self.__model = keras.models.Sequential()

    def __get_model_params(self):
        """
        Load all stored params for a project
        :rtype: dict
        """
        return self.__project_manager.load_model(self.__project_name)

    def __get_layers(self):
        """
        Load a list from model layers
        :rtype: list
        """
        return self.__get_model_params()['layers']

    def __get_epochs(self):
        """
        Load the amount of wanted training epochs
        :rtype: int
        """
        return self.__get_model_params()['epochs']

    def __get_batch_size(self):
        """
        Load the wanted batch-size for training
        :rtype: int
        """
        return self.__get_model_params()['batch-size']

    def __get_validation_split(self):
        """
        Load the validation-split to use during training
        :rtype: float
        """
        return self.__get_model_params()['validation-split']

    def __build_model(self, input_shape):
        """
        Generate a model based on data from the database
        """
        _idx = 0
        layers = self.__get_layers()
        # Iterate over layers sorted by order
        for _layer in sorted(layers, key=lambda x: x['order']):
            if _layer['layerType'] == 'Dense':
                if _idx == 0:
                    self.__model.add(Dense(
                        units=_layer['parameters']['Units'],
                        activation=_layer['parameters']['Activation'].lower(),
                        input_shape=input_shape
                    ))
                else:
                    self.__model.add(Dense(
                        units=_layer['parameters']['Units'],
                        activation=_layer['parameters']['Activation'].lower()
                    ))
            elif _layer['layerType'] == 'Dropout':
                _r = _layer['parameters']['Rate']
                if _r >= 1:
                    _r /= 100.0
                self.__model.add(Dropout(rate=_r))
            else:
                raise ValueError(f'Error building model: there is no layer type {_layer["layerType"]}')

    def train_model(self, x_train, y_train):
        """
        Train a model with given X_train and y_train data, epochs, batch_size and validation split

        :param x_train:
        :type x_train: Series

        :param y_train:
        :type y_train: Series
        """
        self.__build_model(input_shape=ModelManager.__get_input_shape(y_train))

    def store_model(self):
        """
        Write the model to disk
        """
        ...

    def load_model(self):
        """
        Load model from disk
        """
        ...

    def test_model(self):
        """
        Test how good the model scores using the X_test and y_test data, store metrics in database
        """
        ...
