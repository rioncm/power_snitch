Email Notifications
===================

Purpose
-------

Use email when Power Snitch should deliver alerts through an SMTP relay.

Service-level settings
----------------------

The current email service configuration supports:

- SMTP host
- SMTP port
- SMTP username
- SMTP password
- sender email address
- STARTTLS enabled flag

Channel-level settings
----------------------

Email channels currently store:

- one or more destination addresses in a comma-separated list
- optional extra message text

Operational notes
-----------------

- Confirm that the SMTP relay accepts connections from the Power Snitch host.
- Use the diagnostics page to send a test alert before relying on production notifications.

