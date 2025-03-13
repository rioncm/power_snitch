# Setup Form Population Plan

## Current State
- The setup route already retrieves current configuration:
```python
config = {
    'web_interface': db.get_web_interface(),
    'ups': db.get_ups_config(),
    'notifications': {
        'webhook': db.get_webhook_config(),
        'email': db.get_email_config(),
        'sms': db.get_sms_config()
    }
}
```
- The form is created but not populated with these values
- The template renders the form without default values

## Required Changes

### 1. Form Population
Update the `setup` route to populate the form with current values:
```python
form = SetupForm()
if request.method == 'GET':
    # Populate form with current values
    form.web_interface_port.data = config['web_interface'].port
    form.web_interface_password.data = ''  # Don't populate password for security
    form.ups_name.data = config['ups'].name
    form.ups_description.data = config['ups'].description
    form.ups_poll_interval.data = config['ups'].poll_interval
    
    # Webhook settings
    webhook_config = config['notifications']['webhook']
    form.webhook_enabled.data = webhook_config is not None
    if webhook_config:
        form.webhook_url.data = webhook_config.url
        form.webhook_method.data = webhook_config.method
        form.webhook_timeout.data = webhook_config.timeout
    
    # Email settings
    email_config = config['notifications']['email']
    form.email_enabled.data = email_config is not None
    if email_config:
        form.email_smtp_host.data = email_config.smtp_host
        form.email_smtp_port.data = email_config.smtp_port
        form.email_smtp_username.data = email_config.smtp_username
        form.email_smtp_password.data = ''  # Don't populate password for security
        form.email_smtp_use_tls.data = email_config.smtp_use_tls
        form.email_from_email.data = email_config.from_email
        form.email_recipients.data = ','.join(email_config.recipients)
    
    # SMS settings
    sms_config = config['notifications']['sms']
    form.sms_enabled.data = sms_config is not None
    if sms_config:
        form.sms_account_sid.data = sms_config.account_sid
        form.sms_auth_token.data = ''  # Don't populate token for security
        form.sms_from_number.data = sms_config.from_number
```

### 2. Template Updates
- No template changes needed as WTForms will automatically populate the form fields
- The JavaScript toggle functionality will work with the populated values

### 3. Security Considerations
- Password fields:
  - Don't populate actual passwords
  - Show an indicator (e.g., "Password is set") when a password exists
  - Add help text explaining that leaving the field blank keeps the current password
  - Use a placeholder to indicate the field is optional
- Webhook and API tokens:
  - Display the current token value (since these are not sensitive credentials)
  - Add help text explaining the token's purpose
  - Use a placeholder to indicate the field is optional
- General security:
  - Add placeholders to indicate optional fields
  - Add help text for sensitive fields
  - Maintain CSRF protection
  - Validate all inputs on submission

### 4. Testing Plan
1. Test form population with:
   - Empty database (default values)
   - Partially configured database
   - Fully configured database
2. Verify sensitive fields are not populated
3. Verify form submission works with:
   - Unchanged values
   - Modified values
   - New values
4. Test validation with populated values

## Implementation Steps
1. Update the `setup` route with form population code
2. Add placeholders and help text for sensitive fields
3. Test with various database states
4. Document any issues found

## Success Criteria
- Form loads with current database values
- Password fields show "Password is set" indicator when a password exists
- Webhook and API tokens are displayed when set
- Form submission works correctly with both unchanged and modified values
- All validation rules work with populated values
- JavaScript toggle functionality works with populated values

## Next Steps
1. Implement form population in the route
2. Add placeholders and help text
3. Test with various scenarios
4. Document any issues or improvements needed 