#!/usr/bin/env python3
"""
Power Snitch Settings Forms
Handles form validation for system settings.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, BooleanField, SelectField,
    TextAreaField, FloatField, SubmitField
)
from wtforms.validators import (
    DataRequired, NumberRange, URL, Email, Length,
    Optional, ValidationError
)
import json

class UPSSettingsForm(FlaskForm):
    """UPS settings form."""
    
    name = StringField('UPS Name', validators=[DataRequired()])
    model = StringField('Model')
    serial_number = StringField('Serial Number')
    low_battery_threshold = IntegerField('Low Battery Threshold (%)', validators=[
        DataRequired(),
        NumberRange(min=0, max=100, message='Threshold must be between 0 and 100')
    ])
    critical_battery_threshold = IntegerField('Critical Battery Threshold (%)', validators=[
        DataRequired(),
        NumberRange(min=0, max=100, message='Threshold must be between 0 and 100')
    ])
    battery_runtime_threshold = IntegerField('Battery Runtime Threshold (seconds)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Threshold must be positive')
    ])
    submit = SubmitField('Save UPS Settings')

class WebhookSettingsForm(FlaskForm):
    """Webhook settings form."""
    
    enabled = BooleanField('Enable Webhook Notifications')
    url = StringField('Webhook URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    method = SelectField('HTTP Method', choices=[
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH')
    ])
    timeout = IntegerField('Timeout (seconds)', validators=[
        Optional(),
        NumberRange(min=1, max=30, message='Timeout must be between 1 and 30 seconds')
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
    smtp_server = StringField('SMTP Server', validators=[
        Optional(),
        DataRequired(message='SMTP server is required when email is enabled')
    ])
    smtp_port = IntegerField('SMTP Port', validators=[
        Optional(),
        NumberRange(min=1, max=65535, message='Port must be between 1 and 65535')
    ])
    username = StringField('Username', validators=[
        Optional(),
        DataRequired(message='Username is required when email is enabled')
    ])
    password = StringField('Password', validators=[
        Optional(),
        DataRequired(message='Password is required when email is enabled')
    ])
    from_email = StringField('From Email', validators=[
        Optional(),
        Email(message='Please enter a valid email address')
    ])
    to_email = StringField('To Email', validators=[
        Optional(),
        Email(message='Please enter a valid email address')
    ])
    use_tls = BooleanField('Use TLS')
    submit = SubmitField('Save Email Settings')

class SMSSettingsForm(FlaskForm):
    """SMS settings form."""
    
    enabled = BooleanField('Enable SMS Notifications')
    provider = SelectField('Provider', choices=[
        ('twilio', 'Twilio'),
        ('nexmo', 'Nexmo')
    ])
    account_sid = StringField('Account SID', validators=[
        Optional(),
        DataRequired(message='Account SID is required when SMS is enabled')
    ])
    auth_token = StringField('Auth Token', validators=[
        Optional(),
        DataRequired(message='Auth Token is required when SMS is enabled')
    ])
    from_number = StringField('From Number', validators=[
        Optional(),
        DataRequired(message='From Number is required when SMS is enabled')
    ])
    to_number = StringField('To Number', validators=[
        Optional(),
        DataRequired(message='To Number is required when SMS is enabled')
    ])
    submit = SubmitField('Save SMS Settings') 