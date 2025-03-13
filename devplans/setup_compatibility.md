# Setup Page Compatibility Notes

## Current Issues

### 1. Form Structure Mismatch
The setup page needs to match the data structure expected by `web_app.py` and `db.py`:

```python
# Expected form data structure
{
    'web_interface': {
        'port': int,
        'password': str
    },
    'ups': {
        'name': str,
        'description': str,
        'poll_interval': int
    },
    'notifications': {
        'webhook': {
            'enabled': bool,
            'url': str,
            'method': str,
            'timeout': int
        },
        'email': {
            'enabled': bool,
            'smtp': {
                'host': str,
                'port': int,
                'username': str,
                'password': str,
                'use_tls': bool
            }
        },
        'sms': {
            'enabled': bool,
            'twilio': {
                'account_sid': str,
                'auth_token': str,
                'from_number': str
            }
        }
    }
}
```

### 2. Missing Validation
The setup page should include:
- Required field validation
- Port number range validation (1-65535)
- Poll interval validation (minimum 5 seconds)
- URL format validation for webhook
- Email format validation
- Phone number format validation

### 3. Missing Default Values
The setup page should pre-fill with default values from the database models:
- Web interface port: 80
- UPS poll interval: 5 seconds
- Webhook method: 'POST'
- Webhook timeout: 10 seconds
- SMTP port: 587
- SMTP use_tls: true

## Required Changes

### 1. Form Structure
Update the form to use the correct field names and structure:
```html
<form method="POST" action="{{ url_for('setup') }}">
    <!-- Web Interface Settings -->
    <div class="section">
        <h3>Web Interface Settings</h3>
        <div class="form-group">
            <label for="web_interface[port]">Port</label>
            <input type="number" name="web_interface[port]" value="80" min="1" max="65535" required>
        </div>
        <div class="form-group">
            <label for="web_interface[password]">Password</label>
            <input type="password" name="web_interface[password]" required>
        </div>
    </div>

    <!-- UPS Configuration -->
    <div class="section">
        <h3>UPS Configuration</h3>
        <div class="form-group">
            <label for="ups[name]">Name</label>
            <input type="text" name="ups[name]" required>
        </div>
        <div class="form-group">
            <label for="ups[description]">Description</label>
            <textarea name="ups[description]"></textarea>
        </div>
        <div class="form-group">
            <label for="ups[poll_interval]">Poll Interval (seconds)</label>
            <input type="number" name="ups[poll_interval]" value="5" min="5" required>
        </div>
    </div>

    <!-- Notification Settings -->
    <div class="section">
        <h3>Notification Settings</h3>
        
        <!-- Webhook -->
        <div class="notification-section">
            <h4>Webhook</h4>
            <div class="form-group">
                <label>
                    <input type="checkbox" name="notifications[webhook][enabled]">
                    Enable Webhook
                </label>
            </div>
            <div class="webhook-fields">
                <div class="form-group">
                    <label for="notifications[webhook][url]">URL</label>
                    <input type="url" name="notifications[webhook][url]">
                </div>
                <div class="form-group">
                    <label for="notifications[webhook][method]">Method</label>
                    <select name="notifications[webhook][method]">
                        <option value="POST">POST</option>
                        <option value="GET">GET</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="notifications[webhook][timeout]">Timeout (seconds)</label>
                    <input type="number" name="notifications[webhook][timeout]" value="10" min="1">
                </div>
            </div>
        </div>

        <!-- Email -->
        <div class="notification-section">
            <h4>Email</h4>
            <div class="form-group">
                <label>
                    <input type="checkbox" name="notifications[email][enabled]">
                    Enable Email
                </label>
            </div>
            <div class="email-fields">
                <div class="form-group">
                    <label for="notifications[email][smtp][host]">SMTP Host</label>
                    <input type="text" name="notifications[email][smtp][host]">
                </div>
                <div class="form-group">
                    <label for="notifications[email][smtp][port]">SMTP Port</label>
                    <input type="number" name="notifications[email][smtp][port]" value="587">
                </div>
                <div class="form-group">
                    <label for="notifications[email][smtp][username]">Username</label>
                    <input type="text" name="notifications[email][smtp][username]">
                </div>
                <div class="form-group">
                    <label for="notifications[email][smtp][password]">Password</label>
                    <input type="password" name="notifications[email][smtp][password]">
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="notifications[email][smtp][use_tls]" checked>
                        Use TLS
                    </label>
                </div>
            </div>
        </div>

        <!-- SMS -->
        <div class="notification-section">
            <h4>SMS</h4>
            <div class="form-group">
                <label>
                    <input type="checkbox" name="notifications[sms][enabled]">
                    Enable SMS
                </label>
            </div>
            <div class="sms-fields">
                <div class="form-group">
                    <label for="notifications[sms][twilio][account_sid]">Twilio Account SID</label>
                    <input type="text" name="notifications[sms][twilio][account_sid]">
                </div>
                <div class="form-group">
                    <label for="notifications[sms][twilio][auth_token]">Auth Token</label>
                    <input type="password" name="notifications[sms][twilio][auth_token]">
                </div>
                <div class="form-group">
                    <label for="notifications[sms][twilio][from_number]">From Number</label>
                    <input type="tel" name="notifications[sms][twilio][from_number]">
                </div>
            </div>
        </div>
    </div>

    <button type="submit" class="btn btn-primary">Complete Setup</button>
</form>
```

### 2. Client-side Validation
Add JavaScript validation:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate port
        const port = document.querySelector('input[name="web_interface[port]"]');
        if (port.value < 1 || port.value > 65535) {
            alert('Port must be between 1 and 65535');
            return;
        }
        
        // Validate poll interval
        const pollInterval = document.querySelector('input[name="ups[poll_interval]"]');
        if (pollInterval.value < 5) {
            alert('Poll interval must be at least 5 seconds');
            return;
        }
        
        // Validate webhook URL if enabled
        const webhookEnabled = document.querySelector('input[name="notifications[webhook][enabled]"]');
        if (webhookEnabled.checked) {
            const webhookUrl = document.querySelector('input[name="notifications[webhook][url]"]');
            if (!webhookUrl.value) {
                alert('Webhook URL is required when webhook is enabled');
                return;
            }
            try {
                new URL(webhookUrl.value);
            } catch {
                alert('Invalid webhook URL');
                return;
            }
        }
        
        // Validate email settings if enabled
        const emailEnabled = document.querySelector('input[name="notifications[email][enabled]"]');
        if (emailEnabled.checked) {
            const smtpHost = document.querySelector('input[name="notifications[email][smtp][host]"]');
            const smtpUsername = document.querySelector('input[name="notifications[email][smtp][username]"]');
            const smtpPassword = document.querySelector('input[name="notifications[email][smtp][password]"]');
            
            if (!smtpHost.value || !smtpUsername.value || !smtpPassword.value) {
                alert('All SMTP settings are required when email is enabled');
                return;
            }
        }
        
        // Validate SMS settings if enabled
        const smsEnabled = document.querySelector('input[name="notifications[sms][enabled]"]');
        if (smsEnabled.checked) {
            const accountSid = document.querySelector('input[name="notifications[sms][twilio][account_sid]"]');
            const authToken = document.querySelector('input[name="notifications[sms][twilio][auth_token]"]');
            const fromNumber = document.querySelector('input[name="notifications[sms][twilio][from_number]"]');
            
            if (!accountSid.value || !authToken.value || !fromNumber.value) {
                alert('All Twilio settings are required when SMS is enabled');
                return;
            }
        }
        
        form.submit();
    });
    
    // Toggle notification fields based on enabled state
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const fields = this.closest('.notification-section').querySelector('.fields');
            fields.style.display = this.checked ? 'block' : 'none';
        });
    });
});
```

### 3. Error Handling
Add error message display:
```html
{% if form.errors %}
<div class="alert alert-danger">
    <h4>Please correct the following errors:</h4>
    <ul>
        {% for field, errors in form.errors.items() %}
            {% for error in errors %}
                <li>{{ field }}: {{ error }}</li>
            {% endfor %}
        {% endfor %}
    </ul>
</div>
{% endif %}
```

## Implementation Plan

1. Create the setup.html template with the correct form structure
2. Add client-side validation
3. Add error handling
4. Add CSS styling for the form
5. Test the form submission with the backend

Would you like me to proceed with any of these changes? 