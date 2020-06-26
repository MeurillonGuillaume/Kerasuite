import logging
from flask import session, request
from core.modelcomponents import LAYER_OPTIONS
from wtforms import Form, StringField, PasswordField, validators, HiddenField, TextAreaField, SelectMultipleField, \
    SelectField
from wtforms.fields.html5 import IntegerRangeField, IntegerField

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


def get_layer_params(layer_type):
    """
    Request data for all params defined for a certain layer

    :param layer_type:
    :type layer_type: str

    :rtype: dict
    """
    _res = {}
    for _o in LAYER_OPTIONS[layer_type]:
        # Attempt to convert to most fitting datatype, else use String
        try:
            _res[_o] = eval(request.form[_o])
        except Exception:
            _res[_o] = request.form[_o]
    return _res


class LoginForm(Form):
    username = StringField(
        label='Username',
        validators=[
            validators.Length(min=3, message='Username is not long enough'),
            validators.DataRequired(message='A username is required')
        ],
        render_kw={
            'placeholder': 'JohnDoe123',
            'autofocus': True
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
            validators.Regexp('(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$',
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
            validators.Regexp('^[a-zA-Z0-9_ ]{3,64}$',
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
            validators.Regexp('^[a-zA-Z0-9_ ]{3,64}$',
                              message='Project name has to be between 3 - 64 characters and cannot contain special characters'),
            validators.DataRequired(message='Stop messing with the HTML, I need that.')
        ]
    )
    project_newname = StringField(
        label='Project name',
        validators=[
            validators.DataRequired(message='A project name is required'),
            validators.Regexp('^[a-zA-Z0-9_ ]{3,64}$',
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
        names.sort()
        self.column_output.choices = [(name, name) for name in names]

    def set_selected_columns(self, selected):
        """
        Set selected columns
        """
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
        names.sort()
        self.columns.choices = [(name, name) for name in names]

    def set_method_choises(self, choises):
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
        names.sort()
        self.column.choices = [(name, name) for name in names]
