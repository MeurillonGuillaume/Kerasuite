from tensorflow import keras


class ModelManager:
    LAYERS = [
        'Dense',
        'Input',
        'Dropout'
    ]

    def __init__(self):
        self.__model = keras.models.Sequential()
