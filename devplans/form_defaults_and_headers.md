# Form Defaults and Headers Plan

## Current Issues
1. Form defaults not loading:
   - The `setup` route retrieves configuration but doesn't populate form fields
   - Need to populate all non-sensitive fields with current values
   - Need to show indicators for password/token fields

2. Missing webhook headers:
   - No fields for webhook headers in the form
   - Headers are important for authentication and custom data
   - Need to add header management to the form

## Required Changes

### 1. Form Population
Update the `setup` route to properly populate form fields:
```python
@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    form = SetupForm()
    
    # Get current configuration
    config = {
        'web_interface': db.get_web_interface(),
        'ups': db.get_ups_config(),
        'notifications': {
            'webhook': db.get_webhook_config(),
            'email': db.get_email_config(),
            'sms': db.get_sms_config()
        }
    }
    
    if request.method == 'GET':
        # Populate web interface settings
        form.web_interface_port.data = config['web_interface'].port
        
        # Populate UPS settings
        form.ups_name.data = config['ups'].name
        form.ups_description.data = config['ups'].description
        form.ups_poll_interval.data = config['ups'].poll_interval
        
        # Populate webhook settings
        webhook_config = config['notifications']['webhook']
        form.webhook_enabled.data = webhook_config is not None
        if webhook_config:
            form.webhook_url.data = webhook_config.url
            form.webhook_method.data = webhook_config.method
            form.webhook_timeout.data = webhook_config.timeout
            form.webhook_headers.data = json.dumps(webhook_config.headers, indent=2)
        
        # Populate email settings
        email_config = config['notifications']['email']
        form.email_enabled.data = email_config is not None
        if email_config:
            form.email_smtp_host.data = email_config.smtp_host
            form.email_smtp_port.data = email_config.smtp_port
            form.email_smtp_username.data = email_config.smtp_username
            form.email_smtp_use_tls.data = email_config.smtp_use_tls
            form.email_from_email.data = email_config.from_email
            form.email_recipients.data = ','.join(email_config.recipients)
        
        # Populate SMS settings
        sms_config = config['notifications']['sms']
        form.sms_enabled.data = sms_config is not None
        if sms_config:
            form.sms_account_sid.data = sms_config.account_sid
            form.sms_from_number.data = sms_config.from_number
```

### 2. Add Webhook Headers
Update the `SetupForm` class to include webhook headers:
```python
class SetupForm(FlaskForm):
    # ... existing fields ...
    
    # Webhook Settings
    webhook_enabled = BooleanField('Enable Webhook')
    webhook_url = URLField('URL', 
        description="The URL where notifications will be sent",
        validators=[Optional(), URL()])
    webhook_method = SelectField('Method', 
        description="HTTP method to use when sending notifications",
        choices=[('POST', 'POST'), ('GET', 'GET')])
    webhook_timeout = IntegerField('Timeout', 
        description="Maximum time to wait for webhook response (seconds)",
        validators=[Optional(), NumberRange(min=1)])
    webhook_headers = TextAreaField('Headers',
        description="JSON object of headers to send with webhook (e.g., {\"Authorization\": \"Bearer token\"})",
        validators=[Optional()])
```

### 3. Update Template
Add webhook headers field to the template:
```html
<!-- In the webhook section -->
<div class="form-group">
    {{ form.webhook_headers.label }}
    {{ form.webhook_headers(class="form-control", rows=4) }}
    {% if form.webhook_headers.description %}
        <div class="form-text">{{ form.webhook_headers.description }}</div>
    {% endif %}
    {% if form.webhook_headers.errors %}
        {% for error in form.webhook_headers.errors %}
            <div class="text-danger small mt-1">{{ error }}</div>
        {% endfor %}
    {% endif %}
</div>
```

### 4. Form Processing
Update the form processing in the route:
```python
if request.method == 'POST':
    if form.validate():
        try:
            # ... existing processing ...
            
            # Process webhook settings
            if form.webhook_enabled.data:
                headers = {}
                if form.webhook_headers.data:
                    try:
                        headers = json.loads(form.webhook_headers.data)
                    except json.JSONDecodeError:
                        form.webhook_headers.errors.append('Invalid JSON format')
                        return render_template('setup.html', form=form, config=config)
                
                db.update_webhook_config(
                    url=form.webhook_url.data,
                    method=form.webhook_method.data,
                    timeout=form.webhook_timeout.data,
                    headers=headers
                )
```

## Implementation Steps
1. Update the `SetupForm` class to add webhook headers field
2. Modify the `setup` route to properly populate form fields
3. Update the template to include the webhook headers field
4. Add JSON validation for webhook headers
5. Update the database operations to handle headers

## Testing Plan
1. Test form population:
   - Empty configuration
   - Partial configuration
   - Full configuration
2. Test webhook headers:
   - Valid JSON input
   - Invalid JSON input
   - Empty input
3. Test form submission:
   - With headers
   - Without headers
   - With invalid headers

## Success Criteria
- All non-sensitive form fields are populated with current values
- Password/token fields show "is set" indicators when values exist
- Webhook headers are properly displayed and editable
- Form submission correctly processes all fields
- JSON validation works for webhook headers

## Next Steps
1. Implement form field updates
2. Add webhook headers support
3. Test with various configurations
4. Document any issues found 