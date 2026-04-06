Overview
========

Power Snitch is designed to monitor one or more locally attached USB UPS devices and surface problems quickly through a local web UI and notification workflows.

What Power Snitch does
----------------------

- Discovers UPS devices that are visible to local NUT.
- Polls enabled UPS devices on a configurable interval.
- Evaluates a fixed set of power, battery, runtime, and communication conditions.
- Sends alerts through configured notification channels.
- Tracks active conditions, alert history, and recent telemetry samples.
- Provides a browser-based interface for day-to-day administration.

Current application shape
-------------------------

The current implementation is a single-process appliance-style service built around these components:

- **FastAPI web application** for login, dashboard, configuration, diagnostics, and history.
- **SQLite** for application state, users, UPS inventory, channels, rules, and alert history.
- **NUT** as the local UPS discovery and status source.
- **Optional InfluxDB mirror** for external telemetry storage when explicitly configured.
- **systemd service** for long-running operation on Debian-family systems.

Primary workflows
-----------------

1. Install Power Snitch on a Linux host that is physically connected to one or more USB UPS devices.
2. Ensure NUT is configured and returns data through ``upsc``.
3. Start the Power Snitch service and sign in to the web UI.
4. Discover UPS devices, confirm which should be monitored, and set thresholds.
5. Configure notification services and create one or more channels.
6. Map UPS conditions to channels and validate outbound delivery with diagnostics.

Core monitored conditions
-------------------------

Power Snitch currently evaluates the following condition keys:

- ``on_battery``
- ``on_line``
- ``low_battery``
- ``replace_battery``
- ``overload``
- ``shutdown_imminent``
- ``battery_low_pct``
- ``runtime_low``
- ``ups_communication_lost``
- ``unknown_state``

Security model
--------------

Power Snitch currently supports a single local admin user. The initial password is generated during bootstrap and written to the runtime data directory. The password can then be changed through the UI.

Network model
-------------

New installs currently default to listening on ``0.0.0.0:8000`` so the UI can be reached from another trusted system on the LAN. This should be treated as a trusted-network deployment unless HTTPS and reverse-proxy hardening are added separately.

