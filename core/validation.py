import logging
from flask import session, request
from core.modelcomponents import LAYER_OPTIONS
from wtforms import Form, StringField, PasswordField, validators, HiddenField, SubmitField

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
        render_kw={'placeholder': 'JohnDoe123', 'autofocus': True}
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
        render_kw={'placeholder': 'P@$$w0rd', 'autofocus': True}
    )
    new_password = PasswordField(
        label='New password',
        validators=[
            validators.DataRequired('A new password is required'),
            validators.Regexp('(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$',
                              message="Your password must be at least 8 characters, and have a mix of capitalised and lowercase letters, numbers and/or special characters")
        ],
        render_kw={'placeholder': 'MyN3wGr34tP@$$w0rd', 'pattern': '(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$'}
    )
    new_password_validate = PasswordField(
        label='Validate new password',
        validators=[
            validators.EqualTo('new_password', 'New passwords must match')
        ],
        render_kw={'placeholder': 'MyN3wGr34tP@$$w0rd', 'pattern': '(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$'}
    )
