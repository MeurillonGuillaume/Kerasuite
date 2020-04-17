from uuid import uuid4
from tensorflow import keras


class ModelManager:
    def __init__(self, projectname):
        self.__projectname = projectname
        self.__model = keras.models.Sequential()

    def visualize_model(self):
        """
        Create a visual representation of the created model
        :returns: The filename of the newly created image
        :rtype: str
        """
        # Create a unique name
        imagename = f'{self.__projectname}-{uuid4()}.png'
        # Generate the model plot
        keras.utils.plot_model(self.__model,
                               to_file=f'plots/{imagename}',
                               show_layer_names=True,
                               show_shapes=True)
        return imagename

    def add_layer(self):
        ...
