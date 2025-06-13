# UPS Integration Development Plan

## Overview
This plan outlines the steps to integrate UPS monitoring via NUT into Power Snitch, following the core principles of fresh installation only, KISS above all, and platform-first design.

## 1. Database Structure Update (tables.sql)

### Required Tables

#### ups
Primary table for UPS information and configuration:
```sql
CREATE TABLE ups (
    id INTEGER PRIMARY KEY,
    description TEXT,
    -- Basic UPS Info (from NUT)
    name TEXT NOT NULL,           -- device.model
    model TEXT,                   -- ups.model
    serial_number TEXT,           -- ups.serial
    firmware TEXT,                -- ups.firmware
    -- Status Fields (updated by NUT polling)
    status TEXT,                  -- ups.status (OL, OB, LB etc)
    battery_charge REAL,          -- battery.charge (%)
    battery_runtime INTEGER,      -- battery.runtime (seconds)
    load REAL,                    -- ups.load (%)
    input_voltage REAL,           -- input.voltage (V)
    output_voltage REAL,          -- output.voltage (V)
    -- Configuration
    low_battery_threshold INTEGER DEFAULT 20,
    critical_battery_threshold INTEGER DEFAULT 10,
    battery_runtime_threshold INTEGER DEFAULT 300,
    -- Timestamps
    last_poll DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### battery_history
For tracking battery status over time:
```sql
CREATE TABLE battery_history (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    battery_charge REAL,          -- battery.charge
    battery_runtime INTEGER,      -- battery.runtime
    status TEXT,                  -- ups.status
    input_voltage REAL,          -- input.voltage
    output_voltage REAL,         -- output.voltage
    load REAL                    -- ups.load
);
```

### Rationale
- Single `ups` table combining status and configuration
- Simplified schema focusing on essential NUT data
- SQLite-friendly data types
- Minimal foreign key relationships
- Default values for thresholds

## 2. Installation Script Updates (install.sh)

### Required Changes

1. Add NUT package installation:
```bash
# Install NUT
apt-get install -y nut
```

2. Add UPS detection and configuration:
```bash
# Detect UPS
if lsusb | grep -qi "UPS"; then
    # UPS detected, get info from NUT
    systemctl start nut-server
    sleep 2
    UPS_NAME=$(upsc ups 2>/dev/null | grep "device.model" | cut -d: -f2 | xargs)
    UPS_MODEL=$(upsc ups 2>/dev/null | grep "ups.model" | cut -d: -f2 | xargs)
    UPS_SERIAL=$(upsc ups 2>/dev/null | grep "ups.serial" | cut -d: -f2 | xargs)
else
    # Default values
    UPS_NAME="Unknown UPS"
    UPS_MODEL="Unknown"
    UPS_SERIAL=""
fi
```

3. Update defaults.sql template:
```sql
-- UPS default configuration
INSERT INTO ups (name, model, serial_number, description)
VALUES ('${UPS_NAME}', '${UPS_MODEL}', '${UPS_SERIAL}', 'Auto-detected UPS');
```

### Rationale
- Automatic UPS detection during installation
- Graceful fallback to defaults if no UPS present
- No complex configuration required
- Uses standard system tools

## 3. Code Updates

### ups.py Module Changes

1. Simplify the model structure:
- Remove `UPSConfig` class (merge into `UPS`)
- Remove `BatteryHealthConfig` class (use thresholds in `UPS`)
- Keep `BatteryHistory` for time-series data

2. Update methods:
- `get_config()` - simplified to return single UPS instance
- `update_status()` - map NUT variables directly
- `to_dict()` - flatten structure for API responses

3. Add NUT integration:
- Add `poll_nut()` method to fetch current data
- Add error handling for NUT communication
- Add logging for status changes

### Required Additional Files

1. Update `app/services/nut_service.py`:
- Add methods to parse NUT output
- Add error handling for missing UPS
- Add logging for NUT communication

2. Update `app/web/templates/setup.html`:
- Remove NUT configuration fields
- Add view-only UPS information display
- Add description field only

### Rationale
- Simplified code structure
- Direct mapping to NUT data
- Minimal configuration options
- Clear error handling

## Implementation Order

1. Update tables.sql with new schema
2. Update install.sh for UPS detection
3. Update ups.py model
4. Update nut_service.py
5. Update templates
6. Test on Raspberry Pi Zero W

## Testing Requirements

1. Fresh installation tests:
- With UPS connected
- Without UPS connected
- With different UPS models

2. Runtime tests:
- UPS status monitoring
- Battery history recording
- Status display updates

3. Error handling:
- NUT service unavailable
- UPS disconnection
- Invalid data from NUT

## Documentation Updates

1. Add UPS setup section to README
2. Document NUT requirements
3. Add troubleshooting guide for UPS issues
4. Update API documentation 