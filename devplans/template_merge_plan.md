# Template Merge Plan: config.html and settings.html

## Current Situation
We have two templates (`config.html` and `settings.html`) with overlapping functionality for managing system configuration. This creates potential confusion and maintenance issues.

### config.html Features
- UPS Configuration
  - UPS name
  - Poll interval
- Webhook Settings
  - Enable/disable
  - URL configuration
  - Custom headers management
- Email Settings
  - SMTP configuration
  - TLS options
  - Recipients management
- SMS Settings (Twilio)
  - Account credentials
  - Sender number
  - Recipients management
- Notification Triggers
  - Battery level change threshold
  - Load change threshold
  - "Always Notify" events

### settings.html Features
- Web Interface Settings
  - Port configuration
  - Password management with strength indicator
- UPS Configuration
  - Name and description
  - Poll interval
- Notification Settings
  - Webhook configuration
  - Email configuration
  - SMS configuration
- Form validation
- Flash message support
- Modern UI with sections

## Required Changes

### 1. Template Structure
- Keep `settings.html` as the primary template
- Remove `config.html`
- Organize settings into clear sections:
  1. Web Interface
  2. UPS Configuration
  3. Notification Settings
  4. Notification Triggers

### 2. Feature Integration
- Add to `settings.html`:
  - Webhook header management
  - Notification triggers section
  - "Always Notify" events
  - Additional validation for new fields

### 3. UI/UX Improvements
- Maintain consistent styling
- Add collapsible sections for better organization
- Improve form validation feedback
- Add tooltips for complex settings
- Ensure mobile responsiveness

### 4. Backend Integration
- Update routes to handle all settings in one place
- Ensure proper validation for all fields
- Maintain backward compatibility with existing configurations

## Implementation Plan

### Phase 1: Template Update
1. Add new sections to `settings.html`
2. Implement webhook header management
3. Add notification triggers section
4. Add "Always Notify" events section
5. Update form structure and styling

### Phase 2: JavaScript Enhancement
1. Add header management functionality
2. Implement trigger validation
3. Add dynamic form updates
4. Enhance error handling
5. Add loading states

### Phase 3: Backend Updates
1. Update routes to handle all settings
2. Add validation for new fields
3. Update configuration storage
4. Add migration support for existing configs

### Phase 4: Testing
1. Test all form submissions
2. Verify validation
3. Test mobile responsiveness
4. Check backward compatibility
5. Verify notification triggers

## Technical Details

### Form Structure
```html
<form method="POST" action="{{ url_for('settings') }}" id="settings-form">
    <!-- Web Interface Section -->
    <!-- UPS Configuration Section -->
    <!-- Notification Settings Section -->
        <!-- Webhook -->
        <!-- Email -->
        <!-- SMS -->
    <!-- Notification Triggers Section -->
        <!-- Thresholds -->
        <!-- Always Notify Events -->
</form>
```

### JavaScript Functions
```javascript
// Header management
function addHeader() { ... }
function removeHeader() { ... }

// Form validation
function validateForm() { ... }
function validateTriggers() { ... }

// Dynamic updates
function updateFormState() { ... }
```

### CSS Updates
```css
/* New section styles */
.notification-triggers { ... }
.header-management { ... }

/* Responsive adjustments */
@media (max-width: 768px) { ... }
```

## Migration Notes
- Existing configurations will be preserved
- New fields will use default values if not present
- Backward compatibility maintained for existing settings

## Success Criteria
1. All settings from both templates are available in one place
2. Form validation works for all fields
3. UI is consistent and responsive
4. Backend properly handles all settings
5. Existing configurations are preserved
6. No functionality is lost in the merge

## Next Steps
1. Review and approve this plan
2. Begin Phase 1 implementation
3. Test changes incrementally
4. Deploy updates
5. Monitor for any issues 