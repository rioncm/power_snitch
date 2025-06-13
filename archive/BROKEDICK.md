# Known Issues and Required Fixes

## Settings Blueprint Issues
1. `update_webhook_settings()` - Needs update to use new WebhookConfig model and handle recipients
2. `update_email_settings()` - Needs update to use new EmailConfig model and handle recipients
3. `update_sms_settings()` - Needs update to use new SMSConfig model and handle recipients
4. `update_web_interface_settings()` - References non-existent SystemSettings.update_web_interface_settings()
5. Missing import of `current_app` in settings.py

## Model Issues
1. NotificationService
   - Missing implementation of `_send_test_notification()` in service classes
   - Test notification functionality needs to be implemented for each service type
   - Missing proper validation for service-specific fields

2. WebInterface
   - Missing password validation rules
   - Missing port validation (should be between 1-65535)
   - Missing proper handling of setup_completed flag

3. General Model Issues
   - Inconsistent datetime handling (some use String, others DateTime)
   - Missing proper SQLAlchemy event listeners for updated_at timestamps
   - Missing proper cascade delete rules for some relationships

## Form Issues
1. Need to update all forms to match new model structure:
   - WebInterfaceSettingsForm
   - UPSSettingsForm
   - WebhookSettingsForm
   - EmailSettingsForm
   - SMSSettingsForm

## Template Issues
1. setup.html needs update to handle:
   - Multiple email recipients
   - Multiple SMS recipients
   - Proper display of webhook headers
   - Password confirmation field
   - Port validation

## Security Issues
1. Password hashing not implemented in WebInterface model save method
2. Missing CSRF protection on some routes
3. Missing input sanitization for webhook headers
4. Plain text storage of sensitive credentials (SMS auth token, email password)

## Testing Issues
1. Missing unit tests for:
   - Configuration models
   - Settings routes
   - Form validation
   - Notification sending
2. Missing integration tests for:
   - Complete setup flow
   - Configuration updates
   - Notification delivery

## Documentation Issues
1. Missing API documentation
2. Missing setup guide
3. Missing configuration examples
4. Missing troubleshooting guide

## Critical Database Issues
1. Missing UPS Table
   - Error: `sqlite3.OperationalError: no such table: ups`
   - Location: Dashboard route trying to access UPS status
   - Fix Required:
     - Create UPS table schema
     - Add table creation to initial database setup
     - Add migration script for existing installations
   - Impact: Dashboard currently non-functional

2. Missing Notification Service Polymorphic Identity
   - Error: `No such polymorphic_identity 'webhook' is defined`
   - Location: Setup page trying to load notification configurations
   - Fix Required:
     - Define polymorphic identities for notification services
     - Add proper inheritance mapping
     - Update model relationships
   - Impact: Setup page notification sections temporarily disabled

## Dashboard Issues
1. Temporarily Disabled Features
   - UPS Status API endpoint
   - Battery History API endpoint and chart
   - Recent Alerts API endpoint and display
   - Notification Services status display
   - All real-time monitoring features
   - Battery history chart and JavaScript
   - Status indicators and icons

2. Missing Template Features
   - Real-time updates
   - Chart.js integration
   - Status indicators
   - Alert management
   - Service status display

## Future Enhancements
1. Web Interface Advanced Settings
   - Port configuration (moved from setup)
   - SSL/TLS configuration
   - Host binding options
   - Access control settings

2. UPS Configuration Enhancements
   - NUT username/password (if needed beyond localhost)
   - Custom polling intervals
   - Custom threshold settings
   - Advanced NUT driver options
   - Port configuration options 