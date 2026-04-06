Notification Channels
=====================

Concept
-------

A notification service stores provider-level credentials or transport settings. A notification channel is a named, user-facing destination built on top of one service.

Examples:

- one SMTP service with multiple email channels
- one Telegram bot service with multiple chat-specific channels
- one Twilio account with multiple destination numbers

Current channel fields
----------------------

All channels include:

- a unique name
- an associated service
- target-specific settings
- optional extra text appended to alert messages

How channels are used
---------------------

Alert rules reference channels, not services directly. This keeps provider credentials reusable while letting each condition target a clear named destination.

