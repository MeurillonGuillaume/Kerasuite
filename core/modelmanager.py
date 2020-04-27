from tensorflow import keras
from core.projectmanager import ProjectManager


class ModelManager:
    def __init__(self, project_name, project_manager):
        """
        :type project_manager: ProjectManager
        """
        self.__project_manager = project_manager
        self.__project_name = project_name
        self.__model = keras.models.Sequential()

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

    def create_model(self):
        """
        Generate a model based on data from the database
        """
        _layer_data = self.__project_manager.load_model(self.__project_name)
        print(_layer_data)

    def train_model(self):
        """
        Train a model with given X_train and y_train data, epochs, batch_size and validation split
        """
        ...

    def test_model(self):
        """
        Test how good the model scores using the X_test and y_test data, store metrics in database
        """
        ...
