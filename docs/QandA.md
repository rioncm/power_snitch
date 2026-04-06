I reviewed [docs/README.md](/Users/rion/VSCode/power_snitch/docs/README.md) against the current code in [powersnitch.py](/Users/rion/VSCode/power_snitch/powersnitch.py), [modules/config.py](/Users/rion/VSCode/power_snitch/modules/config.py), [modules/monitor.py](/Users/rion/VSCode/power_snitch/modules/monitor.py), and [modules/alerts.py](/Users/rion/VSCode/power_snitch/modules/alerts.py).

The main takeaway is that the README describes the product you want, not the product that exists yet. Right now the repo is a narrow prototype: single-UPS, YAML-configured, email/webhook only, minimal API, and no real web UI. That’s a healthy starting point, but it means the plan should treat this as a substantial product build rather than an incremental polish pass.

**Q&A Draft**
This is the first working intent document, based on your README plus the decisions we just locked.

1. What is Power Snitch?
Power Snitch is a lightweight Linux appliance-style application for monitoring locally USB-connected UPS devices via NUT and sending condition-based alerts.

2. What deployment model are we targeting first?
Debian-family Linux first, including Raspberry Pi OS, installed natively with a script and managed under `systemd`.

3. Is v1 single-UPS or multi-UPS?
Multi-UPS from the start.

4. How are UPS devices enrolled?
The app should auto-discover UPS devices visible through the local NUT installation, then let the user confirm, name, enable, and configure them in the web UI.

5. What is the primary configuration source of truth?
SQLite-backed application data managed through the web UI. Files and environment values should be limited to bootstrap and secrets-oriented setup needs.

6. Is NUT local-only in the first release?
Yes. First release should assume local NUT on the same Linux host and locally attached USB UPS devices.

7. What notification services are required in the first release?
All four:
- Email via SMTP
- Webhook
- Telegram
- SMS via Twilio API

8. What is a notification channel?
A named user-defined instance of a notification service configuration. UPS condition mappings can target one or more channels.

9. How customizable are alert messages in v1?
Use a clear default message format and allow optional user-supplied extra text. No full token-template editor in the first release.

10. What alert behavior is expected?
State-based alerting:
- Send when a condition starts
- Optionally repeat reminders while the condition remains active
- Send recovery/clear notifications when the condition ends

11. What UI is required in the first release?
A server-rendered FastAPI UI with Bootstrap that includes:
- Login/setup flow
- Dashboard
- UPS inventory and status
- UPS enable/disable and per-device settings
- Notification service/channel management
- Condition-to-channel mapping
- Test actions for connectivity and alert delivery
- Basic history and trend views

12. What role does InfluxDB play?
InfluxDB is required in the first release for time-series telemetry, and the UI should include basic graphs from that data.

13. What role does SQLite play?
SQLite should hold app/config/auth/alert mapping/history-style relational data.

14. What authentication model is intended?
Single local admin account with a generated first-boot password and in-app password change.

15. How should the UI be exposed by default?
Bind to localhost by default. Remote/LAN exposure should be an explicit choice, not the default.

16. Is there a public API requirement?
Not for v1. Backend APIs only need to support the bundled UI and internal services; no committed public automation contract yet.

17. What installer experience is intended?
One install script should:
- Install system dependencies
- Install/configure NUT
- Install Python app dependencies
- Set up SQLite and InfluxDB requirements
- Create and enable the `systemd` service
- Generate bootstrap credentials
- Tell the operator how to access the UI safely

**Important Gaps Now Closed**
- This is a full product build, not just a refactor of the existing YAML monitor.
- Multi-UPS is a hard requirement for v1.
- InfluxDB is not optional.
- SMS means Twilio API, not generic webhook glue.
- The UI is first-class and configuration-owned, not a thin wrapper over YAML.

**Assumptions I’d Carry Into The Development Plan**
- FastAPI remains the backend framework.
- UI stays server-rendered rather than becoming a SPA.
- Bootstrap is fine as the starting UI layer.
- We should preserve the lightweight “appliance” feel and avoid requiring external orchestration tools.

The next step is to turn this into a decision-complete development plan with architecture, data model, phased implementation order, and test/acceptance criteria.