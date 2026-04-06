Twilio Notifications
====================

Purpose
-------

Use Twilio when Power Snitch should send SMS alerts.

Service-level settings
----------------------

Twilio services currently store:

- account SID
- auth token
- sender phone number

Channel-level settings
----------------------

Twilio channels currently store:

- destination phone number
- optional extra message text

Operational notes
-----------------

- The configured sender number must be valid for the Twilio account.
- The destination number must be reachable and permitted by the account configuration.

