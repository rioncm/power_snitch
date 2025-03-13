# Dashboard Compatibility Notes

## Current Issues

### 1. Status Data Structure Mismatch
The dashboard template expects status data in a flat structure:
```javascript
{
    'ups.status': 'value',
    'battery.charge': 'value',
    'battery.runtime': 'value',
    'ups.load': 'value'
}
```

But the web_app.py provides a nested structure:
```python
{
    'status': 'value',
    'battery': {
        'charge': value,
        'runtime': value,
        'temperature': value,
        'voltage': value
    },
    'input': {
        'voltage': value,
        'frequency': value,
        'current': value,
        'power': value
    },
    'output': {
        'voltage': value,
        'frequency': value,
        'current': value,
        'power': value
    }
}
```

### 2. API Endpoints Missing
The dashboard uses two API endpoints that don't exist in web_app.py:
- `/api/status`
- `/api/alerts`

### 3. Alert Data Structure Mismatch
The dashboard expects alerts with:
- `timestamp`
- `type`
- `message`
- `resolved`

But the database model shows alerts have:
- `timestamp`
- `alert_type`
- `value`
- `threshold`
- `resolved`
- `resolved_at`

## Required Changes

### 1. Status Data Access
Update the dashboard template to use the correct status data structure:
```html
<span class="status-value" id="upsStatus">{{ status.status }}</span>
<span class="status-value" id="batteryCharge">{{ status.battery.charge }}%</span>
<span class="status-value" id="runtime">{{ status.battery.runtime }}s</span>
<span class="status-value" id="load">{{ status.output.power }}%</span>
```

### 2. Add API Endpoints
Add these routes to web_app.py:
```python
@app.route('/api/status')
@login_required
def api_status():
    """Get current UPS status."""
    status_file = '/opt/power_snitch/data/status.json'
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({'error': 'Status not available'}), 404

@app.route('/api/alerts')
@login_required
def api_alerts():
    """Get recent alerts."""
    alerts = db.get_recent_alerts(limit=10)
    return jsonify({
        'alerts': [{
            'timestamp': alert.timestamp.isoformat(),
            'type': alert.alert_type,
            'message': f"{alert.alert_type}: {alert.value} (threshold: {alert.threshold})",
            'resolved': alert.resolved
        } for alert in alerts]
    })
```

### 3. Chart Data Structure
The chart data structure is correct, but we should add error handling for empty data:
```javascript
data: {
    labels: {{ battery_history.timestamps | tojson | default('[]') }},
    datasets: [{
        label: 'Battery Charge %',
        data: {{ battery_history.charges | tojson | default('[]') }},
        // ...
    }]
}
```

## Implementation Plan

1. First, update the dashboard template to use the correct status data structure
2. Add the missing API endpoints to web_app.py
3. Update the alert display to match the database model
4. Add error handling for empty data in the chart

Would you like me to proceed with any of these changes? 