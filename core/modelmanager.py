from tensorflow import keras


class ModelManager:
    def __init__(self, project_name):
        self.__projectname = project_name
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
        ...

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
