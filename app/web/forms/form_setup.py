#!/usr/bin/env python3
"""
Power Snitch Setup related Forms
Handles form validation for system settings.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, BooleanField, SelectField,
    TextAreaField, FloatField, SubmitField, PasswordField, HiddenField, FieldList
)
from wtforms.validators import (
    DataRequired, NumberRange, URL, Email, Length,
    Optional, ValidationError, EqualTo
)
import json

class ChangePassword(FlaskForm):
    """Form for web interface settings."""
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])

    csrf_token = HiddenField() 

class SetupUPS(FlaskForm):
    """Form for UPS settings."""
    description = StringField('Description', validators=[
        Optional(),
        Length(max=255, message="Description must be less than 255 characters")
        ])
    ups_poll_interval = IntegerField('Poll Interval (seconds)', 
        validators=[
        DataRequired(),
        NumberRange(min=5, message='Poll interval must be at least 5 seconds')])
    
    
    # View-only fields for Setup
    ups_name = StringField('UPS Name', render_kw={'readonly': True})
    model = StringField('Model', render_kw={'readonly': True})
    battery_type = StringField('Battery Type', render_kw={'readonly': True})
    battery_charge = FloatField('Battery Charge (%)', render_kw={'readonly': True})
    battery_runtime = IntegerField('Battery Runtime (minutes)', render_kw={'readonly': True})
    all_info = StringField('All Info', render_kw={'readonly': True})
   
   
    submit = SubmitField('Save UPS Settings')