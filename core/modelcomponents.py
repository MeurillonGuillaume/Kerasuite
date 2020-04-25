# Define all normalization methods here according to the type of normalization applied
NORMALIZATION_METHODS = {
    'Standardization': [
        'StandardScaler',
        'MaxAbsScaler',
        'RobustScaler',
        'Min-Max Scaler'
    ],
    'Normalization': [
        'Normalizer'
    ],
    'Non-Linear transformation': [
        'QuantileTransformer',
        'PowerTransformer'
    ]
}

# Define layer here according to their layer type
LAYERS = {
    'Core layers':
        [
            'Dense',
            'Dropout'
        ]
}

# Define activation functions with explanation of what they do
ACTIVATION_FUNCTIONS = {
    'Linear': 'Basic linear function, in form of f(x) = ax + b',
    'Relu': 'Rectified Linear Unit function',
    'Elu': 'Exponential Linear Unit function',
    'Selu': 'Scaled Exponential Linear Unit function',
    'Sigmoid': 'S-shaped Sigmoid function with limits between y=0 and y=1',
    'Hard Sigmoid': 'Sigmoid function that is computed faster',
    'Softmax': 'Activation function to calculate probability',
    'Softplus': 'Similar to the Relu function, but smoother, also called SmoothRelu',
    'Softsign': 'Similar to Tanh',
    'Exponential': 'Exponential function',
    'Hyperbolic Tangent': 'S-shaped tanh functon with limits between y=-1 and y=1'
}

# Layer options: Which parameters have to be set for a layer
LAYER_OPTIONS = {
    'Dense': {
        'Units': {
            'description': 'The amount of neurons generated for this layer, equals the dimensionality of the output',
            'inputInfo': {
                'type': 'number',
                'min': 0,
                'max': None
            }
        },
        'Activation': {
            'description': 'The type of mathematical function to use as activation function',
            'inputInfo': {
                'type': 'select',
                'values': ACTIVATION_FUNCTIONS
            }
        }
    },
    'Dropout': {
        'Rate': {
            'description': 'The amount of neurons that randomly disabled at once',
            'inputInfo': {
                'type': 'range',
                'min': 0,
                'max': 75
            }
        }
    }
}
