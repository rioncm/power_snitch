# Phase 3: Backend Updates Plan

## Overview
This phase focuses on updating the backend to handle all settings in a unified way, ensuring proper validation, storage, and migration support.

## Template Compatibility Analysis

### Current Template Structure
1. **settings.html**
   - Web interface settings
   - Basic UPS configuration
   - Form structure uses `web_interface.*` and `ups.*` field names
   - Uses Bootstrap form validation
   - Has password strength indicator

2. **config.html**
   - Notification settings (webhook, email, SMS)
   - Notification triggers
   - Form structure uses `notifications.*` and `triggers.*` field names
   - Has dynamic form sections for enabled/disabled notifications
   - Includes webhook header management

### Required Template Updates

1. **Form Field Names**
   - Current backend expects: `web_interface.port`, `ups.name`, etc.
   - Need to ensure all form fields in merged template match the new validation structure
   - Update any JavaScript that references form fields

2. **Form Validation**
   - Current client-side validation in settings.html:
   ```javascript
   function validateForm() {
       const port = document.getElementById('web_interface.port').value;
       const password = document.getElementById('web_interface.password').value;
       // ... existing validation
   }
   ```
   - Need to extend to include notification and trigger validation

3. **Dynamic Sections**
   - Current notification sections use:
   ```javascript
   function toggleNotificationSection(type) {
       const section = document.getElementById(`${type}-settings`);
       const enabled = document.getElementById(`notifications.${type}.enabled`).checked;
       section.style.display = enabled ? 'block' : 'none';
   }
   ```
   - Need to preserve this functionality in merged template

4. **Webhook Headers**
   - Current config.html has header management:
   ```javascript
   function addHeader() {
       const container = document.getElementById('webhook-headers');
       const index = container.children.length;
       // ... header addition logic
   }
   ```
   - Need to integrate this into merged template

### Compatibility Checklist

1. **Form Structure**
   - [ ] All form fields maintain their current names
   - [ ] All required fields are properly marked
   - [ ] Field types match validation requirements
   - [ ] Default values are preserved

2. **JavaScript Functions**
   - [ ] Password strength indicator works
   - [ ] Notification section toggles work
   - [ ] Webhook header management works
   - [ ] Form validation covers all sections

3. **CSS Classes**
   - [ ] Bootstrap form classes are consistent
   - [ ] Custom styling is preserved
   - [ ] Responsive design works

4. **Error Handling**
   - [ ] Flash messages display correctly
   - [ ] Field-level validation errors show properly
   - [ ] Form-level validation errors show properly

### Template Update Plan

1. **Phase 1: Structure Merge**
   - Combine form sections from both templates
   - Maintain existing field names and IDs
   - Preserve Bootstrap structure

2. **Phase 2: JavaScript Integration**
   - Merge validation functions
   - Integrate notification toggles
   - Add webhook header management
   - Update form submission handling

3. **Phase 3: Style Integration**
   - Merge custom CSS
   - Ensure responsive design
   - Test dark mode compatibility

4. **Phase 4: Testing**
   - Test all form submissions
   - Verify validation
   - Check dynamic sections
   - Test error handling

### Success Criteria for Template Compatibility

1. All form fields submit correctly
2. All validation works as expected
3. Dynamic sections toggle properly
4. Error messages display correctly
5. Styling is consistent
6. Responsive design works
7. Dark mode works
8. No JavaScript errors in console

## 1. Route Updates

### Current Routes
```python
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Currently handles web interface and basic UPS settings
    pass

@app.route('/config', methods=['GET', 'POST'])
def config():
    # Currently handles notification and trigger settings
    pass
```

### Required Changes
1. Consolidate routes:
   - Remove `/config` route
   - Update `/settings` to handle all configuration
   - Add proper error handling and validation

2. Update route handler:
```python
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        try:
            # Validate all sections
            validate_web_interface(request.form)
            validate_ups_config(request.form)
            validate_notifications(request.form)
            validate_triggers(request.form)
            
            # Save all settings
            save_settings(request.form)
            
            flash('Settings updated successfully', 'success')
            return redirect(url_for('settings'))
        except ValidationError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash('An error occurred while saving settings', 'error')
            logger.error(f"Settings update error: {str(e)}")
    
    # Load all settings
    settings = load_all_settings()
    return render_template('settings.html', config=settings)
```

## 2. Validation Implementation

### Validation Functions
```python
def validate_web_interface(form_data):
    """Validate web interface settings"""
    port = form_data.get('web_interface.port')
    if not port or not port.isdigit() or not (1 <= int(port) <= 65535):
        raise ValidationError('Port must be between 1 and 65535')
    
    password = form_data.get('web_interface.password')
    if password and len(password) < 8:
        raise ValidationError('Password must be at least 8 characters')

def validate_ups_config(form_data):
    """Validate UPS configuration"""
    name = form_data.get('ups.name')
    if not name:
        raise ValidationError('UPS name is required')
    
    poll_interval = form_data.get('ups.poll_interval')
    if not poll_interval or not poll_interval.isdigit() or int(poll_interval) < 5:
        raise ValidationError('Poll interval must be at least 5 seconds')

def validate_notifications(form_data):
    """Validate notification settings"""
    # Webhook validation
    if form_data.get('notifications.webhook.enabled'):
        url = form_data.get('notifications.webhook.url')
        if not url:
            raise ValidationError('Webhook URL is required when enabled')
        try:
            headers = parse_webhook_headers(form_data)
            validate_webhook_headers(headers)
        except ValueError as e:
            raise ValidationError(f'Invalid webhook headers: {str(e)}')
    
    # Email validation
    if form_data.get('notifications.email.enabled'):
        validate_email_settings(form_data)
    
    # SMS validation
    if form_data.get('notifications.sms.enabled'):
        validate_sms_settings(form_data)

def validate_triggers(form_data):
    """Validate notification triggers"""
    battery_change = form_data.get('triggers.battery_level_change')
    if battery_change and not (0 <= float(battery_change) <= 100):
        raise ValidationError('Battery change threshold must be between 0 and 100')
    
    load_change = form_data.get('triggers.load_change')
    if load_change and not (0 <= float(load_change) <= 100):
        raise ValidationError('Load change threshold must be between 0 and 100')
```

## 3. Configuration Storage

### Database Models
```python
class WebInterfaceConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    port = db.Column(db.Integer, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class UPSConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    poll_interval = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class NotificationConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # webhook, email, sms
    enabled = db.Column(db.Boolean, default=False)
    settings = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class TriggerConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    battery_change_threshold = db.Column(db.Float)
    load_change_threshold = db.Column(db.Float)
    always_notify_events = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Save Functions
```python
def save_settings(form_data):
    """Save all settings to database"""
    with db.session.begin():
        # Save web interface settings
        save_web_interface(form_data)
        
        # Save UPS configuration
        save_ups_config(form_data)
        
        # Save notification settings
        save_notification_settings(form_data)
        
        # Save trigger settings
        save_trigger_settings(form_data)
    
    db.session.commit()

def save_web_interface(form_data):
    """Save web interface settings"""
    config = WebInterfaceConfig.query.first() or WebInterfaceConfig()
    config.port = int(form_data.get('web_interface.port'))
    
    password = form_data.get('web_interface.password')
    if password:
        config.password_hash = generate_password_hash(password)
    
    db.session.add(config)

def save_notification_settings(form_data):
    """Save notification settings"""
    for ntype in ['webhook', 'email', 'sms']:
        config = NotificationConfig.query.filter_by(type=ntype).first()
        if not config:
            config = NotificationConfig(type=ntype)
        
        config.enabled = bool(form_data.get(f'notifications.{ntype}.enabled'))
        config.settings = extract_notification_settings(form_data, ntype)
        db.session.add(config)
```

## 4. Migration Support

### Migration Script
```python
def migrate_existing_config():
    """Migrate existing configuration to new structure"""
    try:
        # Load old configuration
        old_config = load_old_config()
        
        with db.session.begin():
            # Migrate web interface settings
            migrate_web_interface(old_config)
            
            # Migrate UPS configuration
            migrate_ups_config(old_config)
            
            # Migrate notification settings
            migrate_notification_settings(old_config)
            
            # Migrate trigger settings
            migrate_trigger_settings(old_config)
        
        db.session.commit()
        logger.info("Configuration migration completed successfully")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Migration failed: {str(e)}")
        raise
```

### Migration Functions
```python
def migrate_web_interface(old_config):
    """Migrate web interface settings"""
    config = WebInterfaceConfig.query.first() or WebInterfaceConfig()
    config.port = old_config.get('web_interface', {}).get('port', 8080)
    config.password_hash = old_config.get('web_interface', {}).get('password_hash')
    db.session.add(config)

def migrate_notification_settings(old_config):
    """Migrate notification settings"""
    for ntype in ['webhook', 'email', 'sms']:
        old_settings = old_config.get('notifications', {}).get(ntype, {})
        config = NotificationConfig.query.filter_by(type=ntype).first()
        if not config:
            config = NotificationConfig(type=ntype)
        
        config.enabled = old_settings.get('enabled', False)
        config.settings = extract_old_notification_settings(old_settings)
        db.session.add(config)
```

## Implementation Steps

1. **Database Updates**
   - Create new models
   - Run database migrations
   - Add indexes for performance

2. **Route Consolidation**
   - Update settings route
   - Remove config route
   - Add error handling

3. **Validation Implementation**
   - Add validation functions
   - Implement error handling
   - Add logging

4. **Storage Implementation**
   - Implement save functions
   - Add transaction support
   - Add error handling

5. **Migration Support**
   - Create migration script
   - Add rollback support
   - Test migration process

## Testing Plan

1. **Unit Tests**
   - Test validation functions
   - Test save functions
   - Test migration functions

2. **Integration Tests**
   - Test route handling
   - Test database operations
   - Test error handling

3. **Migration Tests**
   - Test with sample old config
   - Test rollback functionality
   - Test data integrity

## Success Criteria

1. All settings are properly validated
2. Settings are correctly saved to database
3. Existing configurations are successfully migrated
4. No data loss during migration
5. Proper error handling and user feedback
6. All tests pass

## Next Steps

1. Review and approve this plan
2. Create database migrations
3. Implement validation functions
4. Implement storage functions
5. Create and test migration script
6. Update routes
7. Run comprehensive tests 