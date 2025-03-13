# Template Debug Plan

## Current Error Analysis
```
jinja2.exceptions.UndefinedError: 'form' is undefined
Location: /opt/power_snitch/templates/setup.html, line 104
Context: {% if form.errors %}
```

### Error Details
1. The error occurs in `setup.html` when trying to access `form.errors`
2. The template is extending `base.html`
3. The error suggests the `form` variable is not being passed to the template

## Debug Steps

### 1. Route Analysis
- [ ] Review `setup` route in `web_app.py`
- [ ] Verify form object creation and passing
- [ ] Check for any conditional form creation

### 2. Template Variable Verification
- [ ] List all variables expected in `setup.html`
- [ ] Compare with variables passed from route
- [ ] Document any missing variables

### 3. Form Handling Review
- [ ] Check form class implementation
- [ ] Verify form initialization
- [ ] Review form validation logic

### 4. Template Structure Check
- [ ] Review `setup.html` template structure
- [ ] Verify template inheritance
- [ ] Check for conditional blocks

## Implementation Plan

### Phase 1: Route Verification
1. Review `setup` route:
```python
@app.route('/setup')
def setup():
    # Current implementation
    return render_template('setup.html', config=config)
```

2. Required changes:
```python
@app.route('/setup')
def setup():
    form = SetupForm()  # Create form instance
    return render_template('setup.html', config=config, form=form)
```

### Phase 2: Form Implementation
1. Create/verify form class:
```python
class SetupForm(FlaskForm):
    # Form fields
    pass
```

2. Add form validation:
```python
    def validate(self):
        # Validation logic
        pass
```

### Phase 3: Template Updates
1. Update error handling:
```html
{% if form and form.errors %}
    <!-- Error display -->
{% endif %}
```

2. Add form rendering:
```html
<form method="POST">
    {{ form.csrf_token }}
    <!-- Form fields -->
</form>
```

## Testing Plan

### 1. Route Testing
- [ ] Test GET request to `/setup`
- [ ] Test POST request to `/setup`
- [ ] Verify form object presence

### 2. Form Testing
- [ ] Test form validation
- [ ] Test error display
- [ ] Test successful submission

### 3. Template Testing
- [ ] Test template rendering
- [ ] Test error display
- [ ] Test form submission

## Success Criteria

1. No template errors
2. Form properly displayed
3. Validation working
4. Error messages displayed correctly
5. Successful form submission

## Next Steps

1. Review and update route implementation
2. Verify form class implementation
3. Update template error handling
4. Test all scenarios
5. Document any additional issues

## Notes

- Keep original templates in archive for reference
- Document all changes made
- Test each change independently
- Maintain backward compatibility 