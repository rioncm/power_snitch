-- Power Snitch Database Schema
-- ==========================

-- Web Interface Settings
CREATE TABLE IF NOT EXISTS web_interface (
    id INTEGER PRIMARY KEY,
    port INTEGER NOT NULL DEFAULT 80,
    password_hash TEXT NOT NULL,
    setup_completed BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- UPS Configuration
CREATE TABLE IF NOT EXISTS ups_config (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    poll_interval INTEGER NOT NULL DEFAULT 5,
    -- NUT-specific fields
    nut_device_name TEXT NOT NULL DEFAULT 'ups',
    nut_driver TEXT NOT NULL DEFAULT 'usbhid-ups',
    nut_port TEXT,
    nut_username TEXT NOT NULL DEFAULT 'admin',
    nut_password TEXT NOT NULL DEFAULT '',
    nut_retry_count INTEGER DEFAULT 3,
    nut_retry_delay INTEGER DEFAULT 5,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Health Check Configuration
CREATE TABLE IF NOT EXISTS health_check (
    id INTEGER PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT 0,
    notification_time TEXT NOT NULL DEFAULT '09:00:00',  -- Default to 9 AM
    last_notification TEXT,  -- Track last notification time
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Battery Health Configuration
CREATE TABLE IF NOT EXISTS battery_health_config (
    id INTEGER PRIMARY KEY,
    low_charge_threshold INTEGER NOT NULL DEFAULT 20,
    warning_charge_threshold INTEGER NOT NULL DEFAULT 50,
    low_runtime_threshold INTEGER NOT NULL DEFAULT 300,  -- 5 minutes in seconds
    low_voltage_threshold REAL,
    high_voltage_threshold REAL,
    temperature_high_threshold REAL,
    temperature_low_threshold REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Battery Health History
CREATE TABLE IF NOT EXISTS battery_health_history (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    charge_percentage INTEGER NOT NULL,
    runtime_seconds INTEGER,
    voltage REAL,
    current REAL,
    temperature REAL,
    energy_stored REAL,
    energy_full REAL,
    battery_date TEXT,
    battery_type TEXT,
    battery_packs INTEGER,
    battery_packs_bad INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Battery Alerts
CREATE TABLE IF NOT EXISTS battery_alerts (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    alert_type TEXT NOT NULL CHECK(alert_type IN (
        'low_charge',
        'low_runtime',
        'low_voltage',
        'high_voltage',
        'high_temperature',
        'low_temperature',
        'bad_packs',
        'replacement_needed'
    )),
    value REAL NOT NULL,
    threshold REAL NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT 0,
    resolved_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Notification Services
CREATE TABLE IF NOT EXISTS notification_services (
    id INTEGER PRIMARY KEY,
    service_type TEXT NOT NULL CHECK(service_type IN ('webhook', 'email', 'sms')),
    enabled BOOLEAN NOT NULL DEFAULT 0,
    last_test TEXT,
    last_test_status BOOLEAN,
    last_test_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(service_type)
);

-- Webhook Configuration
CREATE TABLE IF NOT EXISTS webhook_config (
    id INTEGER PRIMARY KEY,
    service_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'POST',
    timeout INTEGER NOT NULL DEFAULT 10,
    headers TEXT, -- JSON string of headers
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES notification_services(id)
);

-- Email Configuration
CREATE TABLE IF NOT EXISTS email_config (
    id INTEGER PRIMARY KEY,
    service_id INTEGER NOT NULL,
    smtp_host TEXT NOT NULL,
    smtp_port INTEGER NOT NULL DEFAULT 587,
    smtp_username TEXT NOT NULL,
    smtp_password TEXT NOT NULL,
    use_tls BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES notification_services(id)
);

-- Email Recipients
CREATE TABLE IF NOT EXISTS email_recipients (
    id INTEGER PRIMARY KEY,
    email_config_id INTEGER NOT NULL,
    email_address TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_config_id) REFERENCES email_config(id)
);

-- SMS Configuration (Twilio)
CREATE TABLE IF NOT EXISTS sms_config (
    id INTEGER PRIMARY KEY,
    service_id INTEGER NOT NULL,
    twilio_account_sid TEXT NOT NULL,
    twilio_auth_token TEXT NOT NULL,
    twilio_from_number TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES notification_services(id)
);

-- SMS Recipients
CREATE TABLE IF NOT EXISTS sms_recipients (
    id INTEGER PRIMARY KEY,
    sms_config_id INTEGER NOT NULL,
    phone_number TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sms_config_id) REFERENCES sms_config(id)
);

-- Notification Triggers
CREATE TABLE IF NOT EXISTS triggers (
    id INTEGER PRIMARY KEY,
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('battery_level_change', 'load_change', 'always_notify', 'health_check')),
    value INTEGER, -- For battery_level_change and load_change
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Always Notify Events
CREATE TABLE IF NOT EXISTS always_notify_events (
    id INTEGER PRIMARY KEY,
    trigger_id INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('power_failure', 'power_restored', 'low_battery', 'health_check')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trigger_id) REFERENCES triggers(id)
);
