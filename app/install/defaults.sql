-- Insert default UPS configuration
INSERT OR IGNORE INTO ups_config (
    name, description, poll_interval,
    nut_device_name, nut_driver, nut_port,
    nut_username, nut_password, nut_retry_count, nut_retry_delay
) VALUES (
    'ups',
    'Power Snitch UPS',
    60,
    'ups',
    'usbhid-ups',
    'auto',
    'admin',
    '',
    3,
    5
);

-- Insert default web interface settings with default password 'admin'
INSERT OR IGNORE INTO web_interface (port, password_hash, setup_completed) 
VALUES (80, 'scrypt:32768:8:1$pHDt0joiS25zK4F6$fc40e48f064dcbd7031adf2676c01273ff17572ff24fe02ee8f10220fd37627d246c4c78669f9871719af96c0c9fd9de09525fa9213b749d1ae8f457149cd2ef', 0);

-- Insert default health check configuration
INSERT OR IGNORE INTO health_check (enabled, notification_time) VALUES 
(0, '09:00:00');

-- Insert default battery health configuration
INSERT OR IGNORE INTO battery_health_config (
    low_charge_threshold,
    warning_charge_threshold,
    low_runtime_threshold,
    low_voltage_threshold,
    high_voltage_threshold,
    temperature_high_threshold,
    temperature_low_threshold
) VALUES (
    20,    -- low_charge_threshold
    50,    -- warning_charge_threshold
    300,   -- low_runtime_threshold (5 minutes)
    NULL,  -- low_voltage_threshold
    NULL,  -- high_voltage_threshold
    NULL,  -- temperature_high_threshold
    NULL   -- temperature_low_threshold
);

-- Insert notification services (all disabled by default)
INSERT OR IGNORE INTO notification_services (service_type, enabled) VALUES 
('webhook', 0),
('email', 0),
('sms', 0);

-- Insert default triggers
INSERT OR IGNORE INTO triggers (trigger_type, value) VALUES 
('battery_level_change', 10),
('load_change', 50),
('always_notify', NULL),
('health_check', NULL);

-- Insert default always notify events
INSERT OR IGNORE INTO always_notify_events (trigger_id, event_type)
SELECT t.id, e.event_type
FROM triggers t
CROSS JOIN (
    SELECT 'power_failure' as event_type UNION ALL
    SELECT 'power_restored' UNION ALL
    SELECT 'low_battery' UNION ALL
    SELECT 'health_check'
) AS e
WHERE t.trigger_type = 'always_notify'; 