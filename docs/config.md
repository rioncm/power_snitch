Power Snitch Configuration Guide (config.yaml)

Power Snitch is configured using a single YAML file named config.yaml, typically located at /opt/powersnitch/config.yaml. This file defines how the daemon polls the UPS, where it sends alerts, and how it logs and authenticates for email.

⸻

📁 File Location

/opt/powersnitch/config.yaml


⸻

🧱 Configuration Structure

ups:
  poll_interval_seconds: 10
  status_command: "/bin/upsc ups@localhost"

channels:
  webhook_alert:
    type: "webhook"
    url: "https://example.com/hook"
    headers:
      Authorization: "Bearer YOUR_TOKEN"

  admin_email:
    type: "email"
    to:
      - "admin@example.com"

alerts:
  - event: "OB"
    repeat_interval_seconds: 300
    methods:
      - webhook_alert
      - admin_email

  - event: "LB"
    methods:
      - admin_email

logging:
  level: "INFO"
  path: "/var/log/powersnitch.log"
  json_format: true

smtp:
  server: "smtp.example.com"
  port: 587
  username: "user"
  password: "pass"


⸻

🔌 ups

Field	Description
poll_interval_seconds	How often to poll UPS status (in seconds)
status_command	Command to run to retrieve UPS status (typically upsc)


⸻

📣 channels

Defines reusable destinations for alert delivery. Each alert rule references channels by name.

Webhook Channel

Field	Description
type	Must be webhook
url	Target URL for POST requests
headers	Optional dictionary of headers (e.g., for authentication)

Email Channel

Field	Description
type	Must be email
to	List of recipient email addresses


⸻

🚨 alerts

Each alert rule defines a regex event to match against UPS status flags and a list of delivery channels.

Field	Description
event	Regex pattern to match UPS status (e.g., OB, LB, FSD)
methods	List of channel keys to use for delivery
repeat_interval_seconds	Optional minimum time between repeated alerts (in seconds)


⸻

📜 logging

Controls log output for the monitor and alert system.

Field	Description
level	Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
path	File path where logs are written
json_format	Set to true for structured JSON logs (e.g., for Loki)


⸻

✉️ smtp

Used for sending email alerts via a configured SMTP relay.

Field	Description
server	SMTP hostname
port	SMTP port (587 recommended)
username	Login username
password	Login password (in plaintext)


⸻

✅ Best Practices
	•	Use secure HTTPS URLs for webhooks
	•	Use repeat_interval_seconds to avoid alert spamming
	•	Set log level to DEBUG for diagnostics, and INFO for normal operation
	•	Rotate logs at the file system level if running long-term

⸻

📌 Related Topics
	•	Alert Types Reference
	•	System Setup Script
	•	Health & Logs API

For more advanced alert logic or field-based conditions, see future roadmap for v2 support.