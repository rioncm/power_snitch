#!/usr/bin/env python3
"""
Power Snitch Settings Forms
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



class UPSSettingsForm(FlaskForm):
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

class WebhookSettingsForm(FlaskForm):
    """Webhook settings form."""
    
    enabled = BooleanField('Enable Webhook Notifications')
    url = StringField('Webhook URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    method = SelectField('HTTP Method', choices=[
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE')
    ])
    timeout = IntegerField('Timeout (seconds)', validators=[
        Optional(),
        NumberRange(min=1, max=60, message='Timeout must be between 1 and 60 seconds')
    ])
    headers = TextAreaField('Additional Headers (JSON)', validators=[
        Optional(),
        Length(max=1000, message='Headers must be less than 1000 characters')
    ])
    submit = SubmitField('Save Webhook Settings')
    
    def validate_headers(self, field):
        """Validate JSON headers."""
        if field.data:
            try:
                headers = json.loads(field.data)
                if not isinstance(headers, dict):
                    raise ValidationError('Headers must be a valid JSON object')
                for key, value in headers.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        raise ValidationError('Header keys and values must be strings')
            except json.JSONDecodeError:
                raise ValidationError('Invalid JSON format')

class EmailSettingsForm(FlaskForm):
    """Email settings form."""
    
    enabled = BooleanField('Enable Email Notifications')
    smtp_host = StringField('SMTP Server', validators=[
        Optional(),
        DataRequired(message='SMTP server is required when email is enabled')
    ])
    smtp_port = IntegerField('SMTP Port', validators=[
        Optional(),
        NumberRange(min=1, max=65535, message='Port must be between 1 and 65535')
    ])
    smtp_username = StringField('SMTP Username', validators=[
        Optional(),
        DataRequired(message='Username is required when email is enabled')
    ])
    smtp_password = PasswordField('SMTP Password', validators=[
        Optional(),
        DataRequired(message='Password is required when email is enabled')
    ])
    use_tls = BooleanField('Use TLS')
    recipients = FieldList(
        StringField('Email', validators=[Optional(), Email()]),
        min_entries=1
    )
    submit = SubmitField('Save Email Settings')

class SMSSettingsForm(FlaskForm):
    """SMS settings form."""
    
    enabled = BooleanField('Enable SMS Notifications')
    account_sid = StringField('Twilio Account SID', validators=[
        Optional(),
        DataRequired(message='Account SID is required when SMS is enabled')
    ])
    auth_token = PasswordField('Twilio Auth Token', validators=[
        Optional(),
        DataRequired(message='Auth Token is required when SMS is enabled')
    ])
    from_number = StringField('From Number', validators=[
        Optional(),
        DataRequired(message='From Number is required when SMS is enabled')
    ])
    recipients = FieldList(
        StringField('Phone Number', validators=[
            Optional(),
            Length(min=10, max=15, message="Must be a valid phone number")
        ]),
        min_entries=1
    )
    submit = SubmitField('Save SMS Settings')

class WebInterfaceSettingsForm(FlaskForm):
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