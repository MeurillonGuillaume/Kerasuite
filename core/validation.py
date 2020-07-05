import logging

from flask import session, request
from wtforms import Form, StringField, PasswordField, validators, HiddenField, TextAreaField, SelectMultipleField, \
    SelectField, BooleanField
from wtforms.fields.html5 import IntegerRangeField, IntegerField

from core.modelcomponents import LAYER_OPTIONS, ACTIVATION_FUNCTIONS

# Globals
ALLOWED_FILETYPES = ['csv', 'json']


def is_user_logged_in():
    """
    Check if the requester is logged in
    :rtype: bool
    """
    try:
        return session['loggedin']
    except Exception as e:
        logging.debug(f'Session not yet created, creating empty. {e}')
        session['loggedin'] = False
        return 0


def is_file_allowed(filename):
    """
    Check if a filetype is allowed
    :type filename: str
    :rtype: bool
    """
    try:
        return '.' in filename and str(filename).rsplit('.', 1)[1].lower() in ALLOWED_FILETYPES
    except Exception as e:
        logging.error(f'Error in checking if {filename} is allowed: {e}')
        return 0


def post_has_keys(*args):
    """
    Check if a POST request contains all required keys
    :type args: dict
    :rtype: bool
    """
    if request.method == 'POST':
        return all(k in request.form for k in args)
    return 0


def get_has_keys(*args):
    """
    Check if required keys are in a GET request and return data if so

    :param args:
    :type: str

    :rtype: dict
    """
    _isvalid, _res = [], {}
    if request.method == 'GET':
        # Check if items are not empty
        for _item in args:
            _data = str(request.args.get(_item))
            if _data is not None and len(_data.strip()) > 0:
                _isvalid.append(1)
            else:
                _isvalid.append(0)
            try:
                _res[_item] = eval(request.args.get(_item))
            except:
                _res[_item] = str(request.args.get(_item))
        if all(_isvalid):
            return _res
    return


def get_layer_params(form_data, layer_type):
    """
    Request data for all params defined for a certain layer

    :param layer_type:
    :type layer_type: str

    :rtype: dict
    """
    _result = {}
    if layer_type == 'Dense':
        _result['units'] = form_data.units.data
        _result['activation'] = form_data.activation.data
    elif layer_type == 'Dropout':
        _result['rate'] = form_data.rate.data
    return _result


class LoginForm(Form):
    username = StringField(
        label='Username',
        validators=[
            validators.Length(min=3, message='Username is not long enough'),
            validators.DataRequired(message='A username is required'),
            validators.Regexp(
                '^[a-zA-Z0-9_-]{3,64}$',
                message='A username should have between 3 and 64 alphanumeric characters, no special except _ and -.')
        ],
        render_kw={
            'placeholder': 'JohnDoe123',
            'autofocus': True,
            'pattern': '^[a-zA-Z0-9_-]{3,64}$'
        }
    )
    password = PasswordField(
        label='Password',
        validators=[
            validators.Length(min=8, message='The password needs at least 8 characters'),
            validators.DataRequired(message='A password is required')
        ],
        render_kw={'placeholder': 'P@$$w0rd'}
    )


class PasswordUpdateForm(Form):
    old_password = PasswordField(
        label='Old password',
        validators=[
            validators.DataRequired()
        ],
        render_kw={
            'placeholder': 'P@$$w0rd',
            'autofocus': True
        }
    )
    new_password = PasswordField(
        label='New password',
        validators=[
            validators.DataRequired('A new password is required'),
            validators.Regexp(
                '(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$',
                message="Your password must be at least 8 characters, and have a mix of capitalised and lowercase letters, numbers and/or special characters")
        ],
        render_kw={'placeholder': 'MyN3wGr34tP@$$w0rd',
                   'pattern': '(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$'}
    )
    new_password_validate = PasswordField(
        label='Validate new password',
        validators=[
            validators.EqualTo('new_password', 'New passwords must match')
        ],
        render_kw={
            'placeholder': 'MyN3wGr34tP@$$w0rd',
            'pattern': '(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$'
        }
    )


class CreateProjectForm(Form):
    project_name = StringField(
        label='Project name',
        validators=[
            validators.DataRequired(message='A project name is required'),
            validators.Regexp(
                '^[a-zA-Z0-9_ ]{3,64}$',
                message='Project name has to be between 3 - 64 characters and cannot contain special characters')
        ],
        render_kw={
            'placeholder': 'The amazing Hello, World!',
            'pattern': '^[a-zA-Z0-9_ ]{3,64}$'
        }
    )
    project_description = TextAreaField(
        label='Project description',
        validators=[
            validators.Length(max=250, message='The project description cannot be over 250 characters')
        ],
        render_kw={
            'placeholder': 'This project is the most advanced Hello, World! your eyes have ever seen.',
            'rows': 1
        }
    )


class EditProjectForm(Form):
    project_oldname = HiddenField(
        validators=[
            validators.Regexp(
                '^[a-zA-Z0-9_ ]{3,64}$',
                message='Project name has to be between 3 - 64 characters and cannot contain special characters'),
            validators.DataRequired(message='Stop messing with the HTML, I need that.')
        ]
    )
    project_newname = StringField(
        label='Project name',
        validators=[
            validators.DataRequired(message='A project name is required'),
            validators.Regexp(
                '^[a-zA-Z0-9_ ]{3,64}$',
                message='Project name has to be between 3 - 64 characters and cannot contain special characters')
        ],
        render_kw={
            'placeholder': 'The amazing Hello, World!',
            'pattern': '^[a-zA-Z0-9_ ]{3,64}$'
        }
    )
    project_description = TextAreaField(
        label='Project description (optional)',
        validators=[
            validators.Length(max=250, message='The project description cannot be over 250 characters')
        ],
        render_kw={
            'placeholder': 'This project is the most advanced Hello, World! your eyes have ever seen.',
            'rows': 3
        }
    )


class PreprocessingForm(Form):
    project = HiddenField(
        validators=[
            validators.DataRequired(message='Stop messing with the HTML, I need that.')
        ]
    )
    train_test_split = IntegerRangeField(
        label='Which percentage of data should be in the training set?',
        validators=[
            validators.NumberRange(min=50, max=95),
            validators.DataRequired(message='A train-test-split is required.')
        ],
        default=75,
        render_kw={
            'class': 'slider tooltip p-2',
            'oninput': 'this.setAttribute("value", `${this.value}`);',
            'min': 50,
            'max': 95
        }
    )
    random_state = IntegerField(
        label="Custom random state (optional)",
        default=0
    )
    column_output = SelectMultipleField(
        label="Select output column(s)",
        validators=[
            validators.DataRequired(message='At least 1 output column is required!')
        ],
        render_kw={
            'class': 'form-select'
        })

    def set_column_names(self, names):
        """
        Set the values required for the choices input
        """
        if names is not None:
            names.sort()
            self.column_output.choices = [(name, name) for name in names]

    def set_selected_columns(self, selected):
        """
        Set selected columns
        """
        if selected is not None:
            default = []
            for c in self.column_output.choices:
                if c[0] in selected:
                    default.append(c[0])
            self.column_output.data = default


class RenameColumnForm(Form):
    project = HiddenField(
        validators=[
            validators.DataRequired(message='Stop messing with the HTML, I need that.')
        ]
    )
    old_col_name = SelectField(
        label='Column to rename',
        validators=[
            validators.DataRequired(message='An old column name is required')
        ],
        render_kw={'class': 'form-select'}
    )
    new_col_name = StringField(
        label='New column name',
        validators=[
            validators.DataRequired(message="A new column name is required")
        ],
        render_kw={
            'placeholder': 'new-column-name',
            'pattern': '^[a-zA-Z0-9_ ]{2,250}$'
        }
    )

    def set_old_columns(self, names):
        if names is not None:
            names.sort()
            self.old_col_name.choices = [(name, name) for name in names]


class NormalizeForm(Form):
    columns = SelectMultipleField(
        label="Select column(s) to normalize",
        validators=[
            validators.DataRequired('At least one column is required')
        ],
        render_kw={
            'class': 'form-select'
        })
    method = SelectField(
        label="Data normalization method",
        validators=[
            validators.DataRequired('A normalization method is required')
        ]
    )
    project = HiddenField(
        validators=[
            validators.DataRequired(message='Stop messing with the HTML, I need that.')
        ]
    )

    def set_column_names(self, names):
        """
        Set the values required for the choices input
        """
        if names is not None:
            names.sort()
            self.columns.choices = [(name, name) for name in names]

    def set_method_choises(self, choises):
        if choises is not None:
            self.method.choices = [(item, item) for values in choises.values() for item in values]


class DropColumnForm(Form):
    project = HiddenField(
        validators=[
            validators.DataRequired(message='Stop messing with the HTML, I need that.')
        ]
    )
    column = SelectField(
        label="Select a column to drop",
        validators=[
            validators.DataRequired('You need to select which column to drop')
        ],
        render_kw={
            'class': 'form-select'
        })

    def set_column_names(self, names):
        """
        Set the values required for the choices input
        """
        if names is not None:
            names.sort()
            self.column.choices = [(name, name) for name in names]


class ReplaceDataForm(Form):
    project = HiddenField(
        validators=[
            validators.DataRequired(message='Stop messing with the HTML, I need that.')
        ]
    )
    column = SelectField(
        label="Replace values in column",
        validators=[
            validators.DataRequired('You need to select which column to drop')
        ],
        render_kw={
            'class': 'form-select'
        })
    value_old = StringField(
        label='Exact value to replace',
        render_kw={
            'placeholder': 'OldValue123'
        },
        validators=[
            validators.DataRequired('A value to replaced is required'),
            validators.Length(min=1, message='The value to replace should be at least 1 character')
        ]
    )
    value_new = StringField(
        label='Replace all with',
        render_kw={
            'placeholder': 'new-value'
        },
        validators=[
            validators.DataRequired('A new value is required'),
            validators.Length(min=1, message='The new value should be at least 1 character')
        ]
    )

    def set_column_names(self, names):
        """
        Set the values required for the choices input
        """
        if names is not None:
            names.sort()
            self.column.choices = [(name, name) for name in names]


class CreateUserForm(Form):
    username = StringField(
        label='New username',
        validators=[
            validators.DataRequired('A username is required'),
            validators.Regexp(
                '^[a-zA-Z0-9_-]{3,64}$',
                message='A username should have between 3 and 64 alphanumeric characters, no special except _ and -.')
        ],
        render_kw={
            'placeholder': 'TheLegend27',
            'pattern': '^[a-zA-Z0-9_-]{3,64}$'
        }
    )
    password = PasswordField(
        label='Password',
        validators=[
            validators.DataRequired('A password is required'),
            validators.Regexp(
                '(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$',
                message="Your password must be at least 8 characters, and have a mix of capitalised and lowercase letters, numbers and/or special characters")
        ],
        render_kw={
            'pattern': '(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$',
            'placeholder': 'Sup3erS3cr3tP@ssw0rd'
        }
    )
    password_repeat = PasswordField(
        label='Repeat password',
        validators=[
            validators.EqualTo('password', message='Passwords must match!')
        ],
        render_kw={
            'pattern': '(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$',
            'placeholder': 'Sup3erS3cr3tP@ssw0rd'
        }
    )


class CreateLayerForm(Form):
    project = HiddenField(
        validators=[
            validators.DataRequired(message='Stop messing with the HTML, I need that.')
        ]
    )
    new_layer_name = HiddenField(
        validators=[
            validators.DataRequired(message='A layer type is required')
        ],
        render_kw={'id': 'hidden-layertype'}
    )
    new_layer = SelectField(
        label='Layer type',
        choices=[(item, item) for item in LAYER_OPTIONS.keys()],
        render_kw={
            'id': 'model-layer',
            'class': 'form-select'
        }
    )
    layer_description = TextAreaField(
        label='Layer Description (optional)',
        validators=[
            validators.Length(max=250, message='The layer description cannot be over 250 characters')
        ]
    )


class AddDenseLayerForm(Form):
    # Add layer type in subform to double check in app.py
    units = IntegerField(
        label='Units: how many neurons will be created for this layer. This defines the dimensionality of the output',
        validators=[
            validators.NumberRange(min=1, message='A layer must have at least 1 activation unit'),
            validators.DataRequired(message='Units is a required parameters')
        ]
    )
    activation = SelectField(
        label='Activation: the mathematical function used as activation function',
        validators=[
            validators.DataRequired(message='An activation function is required')
        ],
        choices=[(f"{key}", f"{key}: {value}") for key, value in ACTIVATION_FUNCTIONS.items()]
    )


class AddDropoutLayerForm(Form):
    rate = IntegerRangeField(
        label='Rate: a percentage of neurons that are disabled randomly',
        validators=[
            validators.DataRequired('A dropout rate is required'),
            validators.NumberRange(min=0, max=75,
                                   message="The input range for dropout must be between 0 and 75")
        ],
        render_kw={
            'min': 0,
            'max': 100
        }
    )


class ModelOptionsForm(Form):
    project = HiddenField(
        validators=[
            validators.DataRequired(message='Stop messing with the HTML, I need that.')
        ]
    )
    epochs = IntegerRangeField(
        label='Epochs: how many times will the model see the entire training-set',
        validators=[
            validators.DataRequired(message='The amount of epochs is required'),
            validators.NumberRange(min=1, max=1000000, message='The amount of epochs should be between 1 and 1000000')
        ],
        render_kw={
            'min': 1,
            'max': 1000,
            'step': 2,
            'class': 'slider tooltip p-2',
            'oninput': 'this.setAttribute("value", `${this.value}`);',
        }
    )
    batch_size = IntegerRangeField(
        label='Batch size: after how many records will the model update weights (Works most efficient as powers of 2)',
        validators=[
            validators.DataRequired(message='The batch-size is required'),
        ],
        render_kw={
            'min': 2,
            'step': 2,
            'class': 'slider tooltip p-2',
            'oninput': 'this.setAttribute("value", `${this.value}`);',
        }
    )
    early_stopping = BooleanField(
        label='Use early stopping',
        render_kw={'checked': ''}
    )
    model_checkpoints = BooleanField(
        label='Use model checkpoints',
        render_kw={'checked': ''}
    )

    def set_values(self, max_count, current_batchsize=5, current_epochs=25, current_es=False, current_mcp=False):
        self.batch_size.validators.append(
            validators.NumberRange(
                min=1,
                max=max_count,
                message=f'The batch size must be between 1 and {max_count} (the amount of samples in the dataset)'
            )
        )
        self.batch_size.render_kw['max'] = max_count
        self.batch_size.render_kw['value'] = current_batchsize
        self.batch_size.default = current_batchsize
        self.epochs.default = current_epochs
        self.epochs.render_kw['value'] = current_epochs

        self.model_checkpoints.default = current_mcp
        self.early_stopping.default = current_es

        if not current_mcp:
            if 'checked' in self.model_checkpoints.render_kw:
                self.model_checkpoints.render_kw.pop('checked')
        else:
            self.model_checkpoints.render_kw = {'checked': ''}

        if not current_es:
            if 'checked' in self.early_stopping.render_kw:
                self.early_stopping.render_kw.pop('checked')
        else:
            self.early_stopping.render_kw = {'checked': ''}


class EarlyStoppingOptionsForm(Form):
    monitor = SelectField(
        label='Base early stopping on training metric',
        choices=[
            ('loss', 'Loss'),
            ('accuracy', 'Accuracy'),
            ('val_loss', 'Validation loss'),
            ('val_acc', 'Validation accuracy')
        ],
        validators=[
            validators.DataRequired('The metric to monitor is required for early stopping')
        ],
        render_kw={
            'class': 'form-select'
        }
    )
    patience = IntegerRangeField(
        label='Patience: how many epochs of decreased scoring before early stopping kicks in',
        validators=[
            validators.DataRequired('Patience is required for early stopping')
        ],
        default=10,
        render_kw={
            'min': 1,
            'max': 100,
            'step': 2,
            'class': 'slider tooltip p-2',
            'oninput': 'this.setAttribute("value", `${this.value}`);',
        }
    )
    mode = SelectField(
        label='Early stopping mode',
        validators=[
            validators.DataRequired('The early stopping mode is required')
        ],
        choices=[('auto', 'Auto'), ('min', 'Min'), ('max', 'Max')],
        render_kw={
            'class': 'form-select'
        }
    )

    def set_values(self, max_epochs):
        self.patience.validators.append(
            validators.NumberRange(min=1, max=max_epochs,
                                   message=f'The patience value should be between 1 and {max_epochs}')
        )
        self.patience.render_kw['max'] = max_epochs
