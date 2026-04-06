UPS Devices
===========

Device discovery
----------------

Power Snitch discovers UPS devices through local NUT. Discovery depends on ``upsc -l`` returning one or more identifiers.

When discovery succeeds, each device is imported into the UPS inventory and can be reviewed in the UI.

Per-device settings
-------------------

Each UPS entry currently supports:

- display name
- enabled or disabled state
- poll interval in seconds
- low battery percentage threshold
- low runtime threshold in seconds

Recommended workflow
--------------------

1. Use the discovery action after NUT is working.
2. Confirm the imported device name and identifier.
3. Enable only the devices you want Power Snitch to monitor.
4. Adjust thresholds to match the UPS role and shutdown expectations.

