General Configuration
=====================

Configuration source of truth
-----------------------------

Power Snitch uses SQLite as the system of record for application state and user-managed configuration. This includes:

- admin user credentials
- UPS inventory
- notification services
- notification channels
- alert rules
- active conditions
- alert history

Runtime environment
-------------------

The runtime environment file is:

.. code-block:: text

   /opt/powersnitch/runtime.env

Important runtime settings include:

- ``POWERSNITCH_BIND_HOST``
- ``POWERSNITCH_PORT``
- ``POWERSNITCH_SQLITE_PATH``
- ``POWERSNITCH_DATA_DIR``
- ``POWERSNITCH_INITIAL_PASSWORD_FILE``
- ``POWERSNITCH_SESSION_SECRET``
- optional InfluxDB settings

General operating model
-----------------------

The most important configuration work in the UI is:

1. discover UPS devices
2. enable and name devices
3. set per-device threshold values
4. define notification services
5. create named channels
6. attach alert rules to channels

What is not managed in the UI
-----------------------------

Some host-level items remain outside the Power Snitch UI:

- Linux package installation
- firewall policy
- reverse proxy or HTTPS termination
- low-level NUT driver compatibility tuning

