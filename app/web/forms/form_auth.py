#!/usr/bin/env python3
"""
Power Snitch Authentication Forms
Handles form validation for user authentication.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    """Login form."""
    
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In') 