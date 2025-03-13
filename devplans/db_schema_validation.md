# Database Schema Validation Plan

## Overview
This document outlines the necessary changes to ensure proper validation and handling of database fields during the initial setup process.

## Current State
- Database schema is properly defined in `tables.sql`
- Default values are correctly set in `defaults.sql`
- SQLAlchemy models are defined in `db.py`
- Setup form is implemented in `web_app.py`

## Required Changes

### 1. Webhook Headers Validation
Add JSON validation for webhook headers in the setup form to prevent invalid JSON from being stored.

**Location**: `web_app.py`
**Changes**:
```python
def validate_webhook_headers(self, field):
    if field.data:
        try:
            json.loads(field.data)
        except json.JSONDecodeError:
            raise ValidationError('Headers must be valid JSON')
```

### 2. Setup Completion Flag
Ensure the setup_completed flag is properly set when the setup form is submitted successfully.

**Location**: `web_app.py`
**Changes**:
```python
@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if form.validate_on_submit():
        # ... existing code ...
        web_interface = db.get_web_interface()
        web_interface.setup_completed = True
        db.session.commit()
```

### 3. Form Field Population
Ensure all non-sensitive fields are populated with existing values when the setup form is loaded.

**Location**: `web_app.py`
**Changes**:
```python
@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'GET':
        web_interface = db.get_web_interface()
        form.web_interface_port.data = web_interface.port
        # ... populate other non-sensitive fields ...
```

## Implementation Order
1. Add webhook headers validation
2. Implement setup completion flag handling
3. Add form field population

## Testing Requirements
1. Verify webhook headers validation:
   - Test with valid JSON
   - Test with invalid JSON
   - Test with empty field
2. Verify setup completion flag:
   - Check flag is set after successful form submission
   - Verify flag persists after page reload
3. Verify form field population:
   - Check all non-sensitive fields are populated
   - Verify sensitive fields (password) remain empty
   - Confirm values are preserved on form submission errors

## Notes
- No database migrations are needed at this time
- Password hash in defaults.sql is correct and tested
- Focus is on development setup and fresh install scenarios 