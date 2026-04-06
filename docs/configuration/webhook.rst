Webhook Notifications
=====================

Purpose
-------

Use webhooks when Power Snitch should post alerts to an HTTP endpoint.

Service-level settings
----------------------

Webhook services currently support:

- an optional default URL
- optional HTTP headers expressed as JSON

Channel-level settings
----------------------

Webhook channels currently store:

- the target URL
- optional extra message text

Payload model
-------------

The current webhook notification flow sends a simple JSON payload containing:

- ``subject``
- ``message``

Operational notes
-----------------

- Use HTTPS whenever possible.
- If custom headers are required, confirm they are valid JSON when entered in the UI.

