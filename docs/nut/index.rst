NUT Configuration
=================

Power Snitch depends on local NUT for UPS discovery and status polling. If NUT is not installed, disabled, or misconfigured, Power Snitch will run but cannot monitor any UPS devices.

Minimum working state
---------------------

At a minimum, these commands must work:

.. code-block:: bash

   upsc -l
   upsc <ups-name>

Relevant NUT components
-----------------------

Power Snitch currently depends on:

- local UPS drivers
- ``upsd``
- ``upsc``

``upsmon`` is not required for Power Snitch itself.

Required NUT files
------------------

For a local USB UPS deployment, the most important files are:

- ``/etc/nut/nut.conf``
- ``/etc/nut/ups.conf``
- optionally ``/etc/nut/upsd.users`` depending on host policy

Expected mode
-------------

Power Snitch expects:

.. code-block:: text

   MODE=standalone

in ``/etc/nut/nut.conf`` for the common local USB deployment model.

Installer behavior
------------------

The current installer can:

- detect whether NUT already looks compatible
- prompt before changing host NUT config
- back up existing NUT files
- use ``nut-scanner -U`` when available
- fall back to a generic ``usbhid-ups`` definition
- restart NUT services and verify ``upsc -l``

.. toctree::
   :maxdepth: 1

   troubleshooting
   resources

