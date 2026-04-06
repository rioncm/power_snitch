NUT Resources
=============

Useful host commands
--------------------

.. code-block:: bash

   upsc -l
   upsc <ups-name>
   sudo systemctl status nut-driver
   sudo systemctl status nut-server
   sudo journalctl -u nut-server -n 50 --no-pager

Power Snitch files
------------------

- Runtime environment: ``/opt/powersnitch/runtime.env``
- Data directory: ``/opt/powersnitch/data``
- NUT backups created by installer: ``/opt/powersnitch/data/nut-backups``

Common NUT files
----------------

- ``/etc/nut/nut.conf``
- ``/etc/nut/ups.conf``
- ``/etc/nut/upsd.users``
- ``/etc/nut/upsd.conf``

Reference UPS sample
--------------------

A representative UPS status sample used during development is available in:

- ``devplans/ups_dummies/Tripp_Lite__SMC15002URM__usbhid-ups__2.7.4__01.dev``

