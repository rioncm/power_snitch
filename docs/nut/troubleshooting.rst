NUT Troubleshooting
===================

``nut-server`` says NUT is disabled
-----------------------------------

Symptom:

- ``systemctl status nut-server`` reports that ``upsd`` is disabled

Likely cause:

- ``/etc/nut/nut.conf`` is unset or contains ``MODE=none``

Fix:

- set ``MODE=standalone`` in ``/etc/nut/nut.conf``
- restart ``nut-driver`` and ``nut-server``

``nut-server`` exits with “no UPS definitions in ups.conf”
----------------------------------------------------------

Symptom:

- ``upsd`` starts and immediately fails
- foreground output shows ``Warning: no UPS definitions in ups.conf``

Likely cause:

- ``/etc/nut/ups.conf`` is empty or missing valid UPS stanzas

Fix:

- define at least one UPS in ``/etc/nut/ups.conf``
- for many USB HID UPS devices, start with:

.. code-block:: ini

   [ups1]
       driver = usbhid-ups
       port = auto
       desc = "Auto-configured USB UPS"

``upsc -l`` returns nothing
---------------------------

Possible causes:

- drivers are not running
- ``upsd`` is down
- the UPS config does not match the hardware
- the UPS requires a different driver than ``usbhid-ups``

Checks:

.. code-block:: bash

   sudo systemctl status nut-driver
   sudo systemctl status nut-server
   sudo upsd -F
   upsc -l

Power Snitch UI shows no discovered UPS devices
-----------------------------------------------

Power Snitch discovery only works after local NUT is already returning UPS identifiers. Fix NUT first, then use the UPS discovery action in the Power Snitch UI again.

Remote UI access fails
----------------------

Checks:

- confirm ``powersnitch`` is running
- confirm TCP port ``8000`` is open in the host firewall
- confirm the host IP address
- confirm ``POWERSNITCH_BIND_HOST`` in ``/opt/powersnitch/runtime.env``

Useful commands
---------------

.. code-block:: bash

   sudo systemctl status powersnitch
   sudo systemctl status nut-server
   sudo journalctl -u nut-server -n 50 --no-pager
   sudo upsd -F
   upsc -l

