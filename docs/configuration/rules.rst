Alert Rules
===========

Rule model
----------

Each alert rule currently binds:

- one UPS device
- one condition key
- one notification channel
- one repeat interval
- one recovery-alert flag

Alert behavior
--------------

The current monitor loop uses a state-based model:

- send an alert when a condition becomes active
- send reminder alerts when the repeat interval is reached and the condition is still active
- send a recovery alert when the condition clears if recovery notifications are enabled

Supported condition keys
------------------------

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

