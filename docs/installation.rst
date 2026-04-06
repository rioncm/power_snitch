Installation
============

Deployment model
----------------

The expected installation flow is:

1. Clone the repository to the target Linux host.
2. Run the installer from the ``install`` directory.
3. Let the installer copy the codebase into ``/opt/powersnitch``.
4. Start the service with ``systemctl``.
5. Sign in to the web UI from a trusted remote system.

Example install flow
--------------------

.. code-block:: bash

   cd /home/USER_NAME/power_snitch/install
   sudo chmod +x ./install.sh
   sudo ./install.sh

What the installer does
-----------------------

The installer currently:

- Installs operating system dependencies.
- Copies the repository contents into ``/opt/powersnitch``.
- Creates the Python virtual environment under ``/opt/powersnitch/.venv``.
- Installs Python dependencies from ``requirements.txt``.
- Writes ``/opt/powersnitch/runtime.env``.
- Installs and enables the ``powersnitch.service`` unit.
- Validates whether NUT is already compatible.
- Offers to configure NUT automatically for local USB UPS discovery.
- Verifies whether ``upsc -l`` returns any UPS identifiers.

Start the service
-----------------

.. code-block:: bash

   sudo systemctl start powersnitch
   sudo systemctl status powersnitch

Get the generated admin password
--------------------------------

The bootstrap password is written to:

.. code-block:: text

   /opt/powersnitch/data/initial_admin_password.txt

Open the UI
-----------

By default, the application listens on:

.. code-block:: text

   http://<server-ip>:8000

If remote access fails, check:

- The host firewall
- The host IP address
- The Power Snitch bind host in ``/opt/powersnitch/runtime.env``
- The service status with ``systemctl status powersnitch``

Important install paths
-----------------------

- Application root: ``/opt/powersnitch``
- Runtime environment file: ``/opt/powersnitch/runtime.env``
- Data directory: ``/opt/powersnitch/data``
- SQLite database: ``/opt/powersnitch/data/powersnitch.db``
- Initial password file: ``/opt/powersnitch/data/initial_admin_password.txt``
- NUT config backups created by installer: ``/opt/powersnitch/data/nut-backups``

Post-install checks
-------------------

Use these commands during a first-pass validation:

.. code-block:: bash

   sudo systemctl status powersnitch
   sudo systemctl status nut-server
   upsc -l
   curl http://127.0.0.1:8000/healthz

