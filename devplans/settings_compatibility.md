# Settings Page Compatibility Notes

## Current Issues

### 1. Template Structure
The settings.html template currently:
- Does not extend base.html
- Has its own HTML structure and styling
- Contains inline JavaScript
- Has inconsistent class naming with other templates

### 2. Form Data Structure Mismatch
The form field names don't fully match the backend expectations:
- Email SMTP settings use incorrect field names (smtp_host vs smtp.host)
- Password fields don't indicate when they're optional
- Missing validation for required fields when notifications are enabled

### 3. Missing Features
The current template lacks:
- Client-side validation
- Loading states during form submission
- Success/error message styling
- Confirmation dialogs for sensitive changes
- Password strength indicator

## Required Changes

### 1. Template Structure
Update the template to extend base.html and use consistent styling:
```html
{% extends "base.html" %}

{% block title %}Power Snitch - Settings{% endblock %}

{% block content %}
<div class="settings-container">
    <h1 class="text-center mb-4">Settings</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <form method="POST" action="{{ url_for('settings') }}" id="settings-form">
        <!-- Web Interface Settings -->
        <div class="section">
            <h3>Web Interface</h3>
            <div class="form-group">
                <label for="web_port">Port</label>
                <input type="number" id="web_port" name="web_interface[port]" 
                       value="{{ config.web_interface.port }}" min="1" max="65535" required>
            </div>
            <div class="form-group">
                <label for="web_password">Password</label>
                <input type="password" id="web_password" name="web_interface[password]" 
                       placeholder="Leave blank to keep current">
                <div class="password-strength"></div>
            </div>
        </div>

        <!-- UPS Settings -->
        <div class="section">
            <h3>UPS Configuration</h3>
            <div class="form-group">
                <label for="ups_name">UPS Name</label>
                <input type="text" id="ups_name" name="ups[name]" 
                       value="{{ config.ups.name }}" required>
            </div>
            <div class="form-group">
                <label for="ups_description">Description</label>
                <textarea id="ups_description" name="ups[description]" 
                          rows="3">{{ config.ups.description }}</textarea>
            </div>
            <div class="form-group">
                <label for="ups_poll_interval">Poll Interval (seconds)</label>
                <input type="number" id="ups_poll_interval" name="ups[poll_interval]" 
                       value="{{ config.ups.poll_interval }}" min="5" required>
            </div>
        </div>

        <!-- Notification Settings -->
        <div class="section">
            <h3>Notifications</h3>
            
            <!-- Webhook -->
            <div class="notification-section">
                <h4>Webhook</h4>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="notifications[webhook][enabled]" 
                               {% if config.notifications.webhook.enabled %}checked{% endif %}>
                        Enable Webhook
                    </label>
                </div>
                <div class="fields">
                    <div class="form-group">
                        <label for="webhook_url">URL</label>
                        <input type="url" id="webhook_url" name="notifications[webhook][url]" 
                               value="{{ config.notifications.webhook.url }}">
                    </div>
                    <div class="form-group">
                        <label for="webhook_method">Method</label>
                        <select id="webhook_method" name="notifications[webhook][method]">
                            <option value="POST" {% if config.notifications.webhook.method == 'POST' %}selected{% endif %}>POST</option>
                            <option value="GET" {% if config.notifications.webhook.method == 'GET' %}selected{% endif %}>GET</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="webhook_timeout">Timeout (seconds)</label>
                        <input type="number" id="webhook_timeout" name="notifications[webhook][timeout]" 
                               value="{{ config.notifications.webhook.timeout }}" min="1">
                    </div>
                </div>
            </div>

            <!-- Email -->
            <div class="notification-section">
                <h4>Email</h4>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="notifications[email][enabled]" 
                               {% if config.notifications.email.enabled %}checked{% endif %}>
                        Enable Email
                    </label>
                </div>
                <div class="fields">
                    <div class="form-group">
                        <label for="smtp_host">SMTP Host</label>
                        <input type="text" id="smtp_host" name="notifications[email][smtp][host]" 
                               value="{{ config.notifications.email.smtp.host }}">
                    </div>
                    <div class="form-group">
                        <label for="smtp_port">SMTP Port</label>
                        <input type="number" id="smtp_port" name="notifications[email][smtp][port]" 
                               value="{{ config.notifications.email.smtp.port }}">
                    </div>
                    <div class="form-group">
                        <label for="smtp_username">SMTP Username</label>
                        <input type="text" id="smtp_username" name="notifications[email][smtp][username]" 
                               value="{{ config.notifications.email.smtp.username }}">
                    </div>
                    <div class="form-group">
                        <label for="smtp_password">SMTP Password</label>
                        <input type="password" id="smtp_password" name="notifications[email][smtp][password]" 
                               placeholder="Leave blank to keep current">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="notifications[email][smtp][use_tls]" 
                                   {% if config.notifications.email.smtp.use_tls %}checked{% endif %}>
                            Use TLS
                        </label>
                    </div>
                </div>
            </div>

            <!-- SMS -->
            <div class="notification-section">
                <h4>SMS (Twilio)</h4>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="notifications[sms][enabled]" 
                               {% if config.notifications.sms.enabled %}checked{% endif %}>
                        Enable SMS
                    </label>
                </div>
                <div class="fields">
                    <div class="form-group">
                        <label for="twilio_account_sid">Account SID</label>
                        <input type="text" id="twilio_account_sid" name="notifications[sms][twilio][account_sid]" 
                               value="{{ config.notifications.sms.twilio.account_sid }}">
                    </div>
                    <div class="form-group">
                        <label for="twilio_auth_token">Auth Token</label>
                        <input type="password" id="twilio_auth_token" name="notifications[sms][twilio][auth_token]" 
                               placeholder="Leave blank to keep current">
                    </div>
                    <div class="form-group">
                        <label for="twilio_from_number">From Number</label>
                        <input type="tel" id="twilio_from_number" name="notifications[sms][twilio][from_number]" 
                               value="{{ config.notifications.sms.twilio.from_number }}">
                    </div>
                </div>
            </div>
        </div>

        <div class="form-actions">
            <button type="submit" class="btn btn-primary" id="save-settings">
                <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                Save Settings
            </button>
        </div>
    </form>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('settings-form');
    const saveButton = document.getElementById('save-settings');
    const spinner = saveButton.querySelector('.spinner-border');
    
    // Toggle notification fields
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const fields = this.closest('.notification-section').querySelector('.fields');
            fields.style.display = this.checked ? 'block' : 'none';
        });
    });
    
    // Password strength indicator
    const passwordInput = document.getElementById('web_password');
    const strengthIndicator = document.querySelector('.password-strength');
    
    if (passwordInput && strengthIndicator) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            
            if (password.length >= 8) strength++;
            if (password.match(/[a-z]/)) strength++;
            if (password.match(/[A-Z]/)) strength++;
            if (password.match(/[0-9]/)) strength++;
            if (password.match(/[^a-zA-Z0-9]/)) strength++;
            
            const strengthText = ['Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'][strength - 1] || 'Very Weak';
            const strengthClass = ['danger', 'warning', 'info', 'success', 'success'][strength - 1] || 'danger';
            
            strengthIndicator.innerHTML = `
                <div class="progress mt-2" style="height: 5px;">
                    <div class="progress-bar bg-${strengthClass}" role="progressbar" 
                         style="width: ${(strength / 5) * 100}%"></div>
                </div>
                <small class="text-${strengthClass}">${strengthText}</small>
            `;
        });
    }
    
    // Form validation
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate port
        const port = document.getElementById('web_port');
        if (port.value < 1 || port.value > 65535) {
            alert('Port must be between 1 and 65535');
            return;
        }
        
        // Validate poll interval
        const pollInterval = document.getElementById('ups_poll_interval');
        if (pollInterval.value < 5) {
            alert('Poll interval must be at least 5 seconds');
            return;
        }
        
        // Validate webhook if enabled
        const webhookEnabled = document.querySelector('input[name="notifications[webhook][enabled]"]');
        if (webhookEnabled.checked) {
            const webhookUrl = document.getElementById('webhook_url');
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
        
        // Validate email if enabled
        const emailEnabled = document.querySelector('input[name="notifications[email][enabled]"]');
        if (emailEnabled.checked) {
            const smtpHost = document.getElementById('smtp_host');
            const smtpUsername = document.getElementById('smtp_username');
            const smtpPassword = document.getElementById('smtp_password');
            
            if (!smtpHost.value || !smtpUsername.value) {
                alert('SMTP host and username are required when email is enabled');
                return;
            }
        }
        
        // Validate SMS if enabled
        const smsEnabled = document.querySelector('input[name="notifications[sms][enabled]"]');
        if (smsEnabled.checked) {
            const accountSid = document.getElementById('twilio_account_sid');
            const authToken = document.getElementById('twilio_auth_token');
            const fromNumber = document.getElementById('twilio_from_number');
            
            if (!accountSid.value || !fromNumber.value) {
                alert('Twilio account SID and from number are required when SMS is enabled');
                return;
            }
        }
        
        // Show loading state
        saveButton.disabled = true;
        spinner.classList.remove('d-none');
        
        // Submit form
        form.submit();
    });
});
</script>
{% endblock %} 