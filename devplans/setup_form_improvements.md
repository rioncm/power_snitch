# Setup Form Improvements Plan

## Overview
This document outlines improvements needed for the setup form's service settings display and SMTP validation.

## Current State
1. Service settings sections (webhook, email, SMS) only expand when manually enabled
2. SMTP validation needs refinement for hostname format and required fields

## Required Changes

### 1. Service Settings Display
Modify the setup form to automatically expand enabled service sections on page load.

**Location**: `templates/setup.html`
**Changes**:
```html
<!-- Add data-expanded attribute based on enabled state -->
<div class="card mb-4" data-service="webhook" data-expanded="{{ form.webhook_enabled.data|lower }}">
    <!-- ... existing webhook section ... -->
</div>

<div class="card mb-4" data-service="email" data-expanded="{{ form.email_enabled.data|lower }}">
    <!-- ... existing email section ... -->
</div>

<div class="card mb-4" data-service="sms" data-expanded="{{ form.sms_enabled.data|lower }}">
    <!-- ... existing SMS section ... -->
</div>
```

**Location**: `static/js/setup.js`
**Changes**:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize service sections based on enabled state
    document.querySelectorAll('[data-service]').forEach(section => {
        if (section.dataset.expanded === 'true') {
            section.classList.add('show');
            // Update any visual indicators (arrows, etc.)
            const toggle = section.querySelector('.service-toggle');
            if (toggle) {
                toggle.classList.add('active');
            }
        }
    });
});
```

### 2. SMTP Validation
Update email configuration validation to properly handle hostnames and required fields.

**Location**: `web_app.py`
**Changes**:
```python
class SetupForm(FlaskForm):
    # ... existing fields ...

    # Update SMTP host validation
    email_smtp_host = StringField('SMTP Host',
        description="Hostname of your SMTP server (e.g., smtp.example.com)",
        validators=[
            Optional(),
            Regexp(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$',
                   message='Invalid hostname format')
        ])
    
    # Make username and password optional
    email_smtp_username = StringField('Username',
        description="SMTP server username (optional)")
    email_smtp_password = PasswordField('Password',
        description="SMTP server password (optional)")
    
    # Add required email fields
    email_from = EmailField('From Address',
        description="Email address to send notifications from",
        validators=[DataRequired(), Email()])
    
    email_recipients = FieldList(EmailField('Recipient',
        validators=[DataRequired(), Email()]),
        min_entries=1,
        description="At least one recipient is required")

    def validate(self):
        if not super().validate():
            return False
        
        # Additional validation for email configuration
        if self.email_enabled.data:
            if not self.email_from.data:
                self.email_from.errors.append('From address is required')
                return False
            
            if not self.email_recipients.data or not any(self.email_recipients.data):
                self.email_recipients.errors.append('At least one recipient is required')
                return False
        
        return True
```

## Implementation Order
1. Update service settings display logic
2. Implement SMTP validation changes
3. Add client-side validation for email fields

## Testing Requirements
1. Service Settings Display:
   - Verify sections expand automatically when enabled
   - Test page reload with different service combinations enabled
   - Confirm visual indicators (arrows) update correctly
   - Test manual toggling still works

2. SMTP Validation:
   - Test valid hostname formats:
     - Single domain (example.com)
     - Subdomain (mail.example.com)
     - Multiple subdomains (smtp.mail.example.com)
   - Test invalid hostname formats
   - Verify username/password are optional
   - Test required from address validation
   - Test required recipient validation
   - Verify validation works with form submission

## Notes
- Hostname regex allows for standard domain formats
- Email validation maintains existing security measures
- Service sections should maintain their state across form submissions 