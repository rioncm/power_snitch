# Template Merge Plan (Frontend Only)

## Overview
This plan focuses on merging `config.html` and `settings.html` templates while keeping the backend routes separate. This allows us to test the frontend changes independently before updating the backend.

## Phase 1: Structure Merge

### 1. Create New Template Structure
```html
{% extends "base.html" %}

{% block title %}Power Snitch - Settings{% endblock %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-12">
            <h1 class="mb-4">Settings</h1>
            
            <!-- Web Interface Settings -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">Web Interface</h5>
                </div>
                <div class="card-body">
                    <form method="POST" action="{{ url_for('settings') }}" id="web-interface-form">
                        <!-- Existing web interface fields from settings.html -->
                    </form>
                </div>
            </div>

            <!-- UPS Configuration -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">UPS Configuration</h5>
                </div>
                <div class="card-body">
                    <form method="POST" action="{{ url_for('settings') }}" id="ups-form">
                        <!-- Existing UPS fields from settings.html -->
                    </form>
                </div>
            </div>

            <!-- Notification Settings -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">Notification Settings</h5>
                </div>
                <div class="card-body">
                    <form method="POST" action="{{ url_for('config') }}" id="notification-form">
                        <!-- Notification fields from config.html -->
                    </form>
                </div>
            </div>

            <!-- Notification Triggers -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">Notification Triggers</h5>
                </div>
                <div class="card-body">
                    <form method="POST" action="{{ url_for('config') }}" id="triggers-form">
                        <!-- Trigger fields from config.html -->
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_css %}
<style>
    /* Combine CSS from both templates */
    .card {
        margin-bottom: 1.5rem;
    }
    
    .form-section {
        margin-bottom: 1rem;
    }
    
    .header-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .header-row .btn {
        padding: 0.25rem 0.5rem;
    }
</style>
{% endblock %}

{% block extra_js %}
<script>
    // Combine JavaScript from both templates
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize password strength indicator
        initPasswordStrength();
        
        // Initialize notification toggles
        initNotificationToggles();
        
        // Initialize webhook header management
        initWebhookHeaders();
        
        // Initialize form validation
        initFormValidation();
    });

    // Password strength indicator (from settings.html)
    function initPasswordStrength() {
        const passwordInput = document.getElementById('web_interface.password');
        const strengthIndicator = document.getElementById('password-strength');
        
        if (passwordInput && strengthIndicator) {
            passwordInput.addEventListener('input', function() {
                const password = this.value;
                const strength = calculatePasswordStrength(password);
                updateStrengthIndicator(strength);
            });
        }
    }

    // Notification toggles (from config.html)
    function initNotificationToggles() {
        const notificationTypes = ['webhook', 'email', 'sms'];
        notificationTypes.forEach(type => {
            const toggle = document.getElementById(`notifications.${type}.enabled`);
            const section = document.getElementById(`${type}-settings`);
            
            if (toggle && section) {
                toggle.addEventListener('change', function() {
                    section.style.display = this.checked ? 'block' : 'none';
                });
            }
        });
    }

    // Webhook header management (from config.html)
    function initWebhookHeaders() {
        const addButton = document.getElementById('add-header');
        const container = document.getElementById('webhook-headers');
        
        if (addButton && container) {
            addButton.addEventListener('click', function() {
                addHeader();
            });
        }
    }

    function addHeader() {
        const container = document.getElementById('webhook-headers');
        const index = container.children.length;
        
        const headerRow = document.createElement('div');
        headerRow.className = 'header-row mb-2';
        headerRow.innerHTML = `
            <input type="text" class="form-control" name="notifications.webhook.headers[${index}][key]" placeholder="Header name">
            <input type="text" class="form-control" name="notifications.webhook.headers[${index}][value]" placeholder="Header value">
            <button type="button" class="btn btn-danger" onclick="removeHeader(this)">Remove</button>
        `;
        
        container.appendChild(headerRow);
    }

    function removeHeader(button) {
        button.closest('.header-row').remove();
    }

    // Form validation (combined from both templates)
    function initFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!validateForm(this)) {
                    e.preventDefault();
                }
            });
        });
    }

    function validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        return isValid;
    }
</script>
{% endblock %}
```

## Phase 2: Testing Plan

### 1. Form Submission Testing
- Test each form independently:
  - Web Interface form → `/settings`
  - UPS form → `/settings`
  - Notification form → `/config`
  - Triggers form → `/config`

### 2. Functionality Testing
- Password strength indicator
- Notification section toggles
- Webhook header management
- Form validation
- Error message display

### 3. Visual Testing
- Responsive design
- Dark mode compatibility
- Bootstrap styling
- Custom CSS

### 4. Browser Testing
- Chrome
- Firefox
- Safari
- Edge

## Implementation Steps

1. **Create New Template**
   - Create `settings_merged.html`
   - Copy structure from plan
   - Keep existing form actions

2. **Copy Existing Content**
   - Copy form fields from `settings.html`
   - Copy form fields from `config.html`
   - Maintain all IDs and names

3. **Add JavaScript**
   - Copy password strength code
   - Copy notification toggle code
   - Copy webhook header code
   - Copy form validation code

4. **Add CSS**
   - Copy custom styles
   - Ensure no conflicts
   - Test dark mode

5. **Testing**
   - Test each form submission
   - Test all JavaScript functions
   - Test responsive design
   - Test dark mode

## Success Criteria

1. All forms submit to correct endpoints
2. All JavaScript functions work
3. All CSS styles are applied correctly
4. No console errors
5. Responsive design works
6. Dark mode works
7. All validation works

## Next Steps

1. Create `settings_merged.html`
2. Test each section independently
3. Fix any issues found
4. Get approval for merged template
5. Plan backend updates 