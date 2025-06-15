Power Snitch Alert Reference

This page documents the possible alerts that Power Snitch can detect based on UPS telemetry gathered via NUT (upsc). Alert matching is driven by regular expression (regex) patterns matched against the UPS status string or derived metrics.

⸻

⚡ Power and Line Status Alerts

Alert Name	Regex Pattern	Description
on_battery	OB	UPS is running on battery (power outage)
on_line	OL	Utility power is online
low_battery	LB	Battery charge is critically low
replace_battery	RB	Battery needs to be replaced
overload	OVER	UPS load is too high
shutdown_imminent	FSD	Forced shutdown has been initiated


⸻

🔋 Battery and Runtime Conditions (Custom)

These alerts are based on battery or voltage values and require conditional logic. Power Snitch v1 supports regex matching, but future versions may support thresholds.

Alert Name	Condition Example	Description
battery_low_pct	battery.charge < 25	Battery is below 25%
runtime_low	battery.runtime < 300	Runtime remaining is under 5 minutes


⸻

❗ Error and Communication Alerts

Alert Name	Regex Pattern	Description
ups_communication_lost	ERROR	UPS is not responding to upsc queries
unknown_state	UNKNOWN	Unexpected or missing UPS state received


⸻

🧪 Manufacturer-Specific Flags

These may vary by vendor and UPS model.

Flag	Description
CAL	Battery calibration in progress
TRIM	UPS voltage trim engaged
BOOST	UPS voltage boost engaged
CHRG	Battery is charging
DISCHRG	Battery is discharging


⸻

✅ Example Configuration

channels:
  webhook_alert:
    type: "webhook"
    url: "https://example.com/notify"
    headers:
      Authorization: "Bearer TOKEN"

  admin_email:
    type: "email"
    to:
      - "admin@example.com"

alerts:
  - event: "OB"
    methods:
      - webhook_alert
      - admin_email

  - event: "LB"
    repeat_interval_seconds: 600
    methods:
      - admin_email

  - event: "FSD"
    methods:
      - admin_email

💡 Tip: Use regex alternation (e.g., OB|LB) to group multiple conditions in one alert rule.

⸻

For advanced UPS-specific flags, consult your model’s upsc output and adapt the regex patterns accordingly.