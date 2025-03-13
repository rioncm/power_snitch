

-- Insert default UPS configuration
INSERT OR IGNORE INTO ups_config (name, description, poll_interval) VALUES 
('ups', 'Default UPS Configuration', 5);

-- Insert default web interface settings with bcrypt hashed password "password"
INSERT OR IGNORE INTO web_interface (port, password_hash, setup_completed) 
VALUES (80, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyDAXxqXqXqXqX', 0);

-- Insert default health check configuration
INSERT OR IGNORE INTO health_check (enabled, notification_time) VALUES 
(0, '09:00:00');

-- Insert default battery health configuration
INSERT OR IGNORE INTO battery_health_config (
    low_charge_threshold,
    warning_charge_threshold,
    low_runtime_threshold
) VALUES (20, 50, 300);

-- Insert notification services (all disabled by default)
INSERT OR IGNORE INTO notification_services (service_type, enabled) VALUES 
('webhook', 0),
('email', 0),
('sms', 0);

-- Insert default triggers
INSERT OR IGNORE INTO triggers (trigger_type, value) VALUES 
('battery_level_change', 5),
('load_change', 5),
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