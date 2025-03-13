# Setup Data Handling Fixes Plan

## Current Issues

1. **Database Schema Mismatch**
   - The `web_interface` table has inconsistent column naming between SQLAlchemy model and SQL initialization
   - Model uses `setup_completed` while SQL uses `setup_complete`
   - This causes initialization errors and potential data inconsistencies

2. **Notification Service Configuration**
   - `get_webhook_config()`, `get_email_config()`, and `get_sms_config()` methods return nested dictionaries
   - The structure doesn't match what the setup route expects
   - This leads to AttributeError when trying to access configuration properties

3. **Webhook Headers Handling**
   - Webhook headers are stored as JSON strings in the database
   - Current code doesn't properly handle JSON serialization/deserialization
   - This can lead to data corruption or invalid JSON errors

4. **Password/Token Handling**
   - Inconsistent handling of sensitive fields across notification types
   - Some password/token fields are not properly preserved when empty
   - No standardized approach to handling existing credentials

5. **Error Handling**
   - Database operations lack proper error handling
   - Missing transaction management
   - Inconsistent error reporting

## Required Changes

### 1. Database Schema Fix
```sql
-- Update web_interface table creation
CREATE TABLE IF NOT EXISTS web_interface (
    id INTEGER PRIMARY KEY,
    port INTEGER NOT NULL DEFAULT 80,
    password_hash TEXT NOT NULL,
    setup_completed BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Notification Service Methods
```python
def get_webhook_config(self):
    """Get webhook notification configuration."""
    session = self.get_session()
    try:
        service = session.query(NotificationService).filter_by(service_type='webhook').first()
        return service.webhook_config if service else None
    finally:
        session.close()

def get_email_config(self):
    """Get email notification configuration."""
    session = self.get_session()
    try:
        service = session.query(NotificationService).filter_by(service_type='email').first()
        return service.email_config if service else None
    finally:
        session.close()

def get_sms_config(self):
    """Get SMS notification configuration."""
    session = self.get_session()
    try:
        service = session.query(NotificationService).filter_by(service_type='sms').first()
        return service.sms_config if service else None
    finally:
        session.close()
```

### 3. Webhook Headers Handling
```python
def update_webhook_config(self, url, method='POST', timeout=30, headers=None):
    """Update webhook configuration."""
    session = self.get_session()
    try:
        service = session.query(NotificationService).filter_by(service_type='webhook').first()
        if not service:
            service = NotificationService(service_type='webhook')
            session.add(service)
        
        if not service.webhook_config:
            service.webhook_config = WebhookConfig()
        
        service.enabled = True
        service.webhook_config.url = url
        service.webhook_config.method = method
        service.webhook_config.timeout = timeout
        service.webhook_config.headers = json.dumps(headers) if headers else None
        
        session.commit()
    finally:
        session.close()
```

### 4. Standardized Password/Token Handling
```python
def update_notification_service(self, service_type, enabled=None, **kwargs):
    """Update notification service settings."""
    session = self.get_session()
    try:
        service = session.query(NotificationService).filter_by(service_type=service_type).first()
        if not service:
            service = NotificationService(service_type=service_type)
            session.add(service)
        
        if enabled is not None:
            service.enabled = enabled
        
        if service_type == 'webhook':
            if 'webhook_config' in kwargs:
                config = service.webhook_config or WebhookConfig()
                for key, value in kwargs['webhook_config'].items():
                    if key == 'headers' and value:
                        config.headers = json.dumps(value)
                    else:
                        setattr(config, key, value)
                service.webhook_config = config
        
        elif service_type == 'email':
            if 'email_config' in kwargs:
                config = service.email_config or EmailConfig()
                for key, value in kwargs['email_config'].items():
                    if key == 'smtp_password' and not value:
                        continue  # Skip empty password updates
                    setattr(config, key, value)
                service.email_config = config
        
        elif service_type == 'sms':
            if 'sms_config' in kwargs:
                config = service.sms_config or SMSConfig()
                for key, value in kwargs['sms_config'].items():
                    if key == 'auth_token' and not value:
                        continue  # Skip empty token updates
                    setattr(config, key, value)
                service.sms_config = config
        
        session.commit()
    finally:
        session.close()
```

### 5. Error Handling
```python
def update_web_interface(self, port=None, password=None, setup_completed=None):
    """Update web interface settings."""
    session = self.get_session()
    try:
        web_interface = session.query(WebInterface).first()
        if not web_interface:
            web_interface = WebInterface()
            session.add(web_interface)
        
        if port is not None:
            web_interface.port = port
        if password is not None:
            web_interface.password_hash = generate_password_hash(password)
        if setup_completed is not None:
            web_interface.setup_completed = setup_completed
        
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating web interface: {str(e)}")
        raise
    finally:
        session.close()
```

## Implementation Order

1. Database schema fix
   - Update SQL initialization script
   - Verify table creation
   - Test with existing data

2. Notification service methods
   - Update getter methods
   - Update setup route to handle new return types
   - Test with existing configurations

3. Webhook headers handling
   - Update webhook configuration methods
   - Add JSON validation
   - Test with various header formats

4. Password/token handling
   - Standardize sensitive field handling
   - Update form processing
   - Test with existing credentials

5. Error handling
   - Add transaction management
   - Implement proper error logging
   - Test error scenarios

## Testing Plan

1. **Database Schema**
   - Test fresh installation
   - Test upgrade from existing installation
   - Verify data integrity

2. **Notification Services**
   - Test each service type independently
   - Test enabling/disabling services
   - Verify configuration persistence

3. **Webhook Headers**
   - Test valid JSON headers
   - Test invalid JSON handling
   - Verify header persistence

4. **Sensitive Data**
   - Test password/token updates
   - Test empty password/token handling
   - Verify existing credentials preservation

5. **Error Handling**
   - Test database connection errors
   - Test invalid data scenarios
   - Verify error logging

## Success Criteria

1. All database operations complete successfully
2. No AttributeError exceptions in setup route
3. Webhook headers properly stored and retrieved
4. Passwords and tokens preserved when not updated
5. Proper error handling and logging
6. All tests pass
7. No data loss during updates

## Rollback Plan

1. Backup database before changes
2. Document current state
3. Prepare rollback scripts
4. Test rollback procedures

## Next Steps

1. Review and approve plan
2. Create database backup
3. Implement changes in order
4. Run test suite
5. Deploy changes
6. Monitor for issues
7. Document changes 