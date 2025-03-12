-- Power Snitch Default Configuration
-- ================================

-- Insert default web interface settings with hashed password "password"
-- Using bcrypt hash of "password"
INSERT OR IGNORE INTO web_interface (port, password_hash) VALUES 
(8080, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyDAXxqXqXqXqX');

-- Insert default UPS configuration
INSERT OR IGNORE INTO ups_config (name, description, poll_interval) VALUES 
('ups', 'Default UPS Configuration', 5);

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
CROSS JOIN (VALUES 
    ('power_failure'),
    ('power_restored'),
    ('low_battery'),
    ('health_check')
) AS e(event_type)
WHERE t.trigger_type = 'always_notify'; 