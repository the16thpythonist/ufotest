==================
Current Test Setup
==================

Currently a UFO camera test setup is located in the facilities of the "DAQ-Lab" within the
`Institute of Data Processing and Electronics (IPE) <https://www.ipe.kit.edu/>`_. The DAQ-Lab is a single room
on the second floor of the container building next to the main institute building.

Important devices
-----------------

Router
~~~~~~

Since ufotest is in part a web application, the network configuration of the setup is an important detail of the
current test setup. All machines in the DAQ-Lab are connected to a Netgear router. Within the KIT subnet (also includes
generic VPN access) this router can be addressed by the url :code:`daq-lab.ipe.kit.edu`. Entering this URL into the
browser will redirect to the login page of the web dashboard of the router. Within the local network, the router has
the static IP address :code:`192.168.1.1`.

Test PC
~~~~~~~

The camera is connected to a dedicated test PC. The PC is running OpenSUSE as the operating system. Within the local
network this test PC has the IP address :code:`192.168.1.100`.

This PC is the one running the "ufotest" application. A systemd service by the name "ufotest" is configured to start
every time the PC is started as well. It will run the following ufotest command:

.. code-block:: console

    ufotest ci serve

This command starts the ufotest web service, which accepts the incoming push notifactions and serves the web interface
of the PC. By these means the ufotest web application should be available whenever the PC is running. The ufotest
application is configured to listen to port 8030, which means that from within the local network the web interface is
available under the URL :code:`http://192.168.1.100:8030`.

Additionally the PC also maintains a secure shell access server (SSH). The main user of the system is called "ufo"
with the following credentials:

- *username*: **ufo**
- *password*: **xxxxxxxx**

This PC is furthermore directly connected to the FPGA board that controls the camera via one of its PCIe sockets.
Additionally the PC has a USB connection to an appropriate programmer device, which is connected to the FPGA board all
the time, which allows the reprogramming of the FPGA.

Network Sockets
~~~~~~~~~~~~~~~

Another important component is the network controlled socket bar. It can be used to control the state of up to 4
independent power sockets. Currently only one of it's ports is used to plug the test PC into. Within the local network
it has the IP address :code:`????`. Using a browser to access the web server of this device redirects to the control
panel of the device. To access the control panel the following credentials are needed:

- *username*: **admin**
- *password*: **xxxxxx**

The control panel can be used to switch individual sockets off and on. The test PC is connected to the socket with
index "1".

The Camera
~~~~~~~~~~

???

Network Configuration
---------------------

Port Forwarding
~~~~~~~~~~~~~~~

The router has the URL "daq-lab.ipe.kit.edu" which can be accessed from anywhere within the KIT subnet. All services
used by this setup use this fact to in turn also expose their own functionality to the broader scope of the entire
KIT subnet. The router is configured with a number of port forwarding rules, which redirect traffic to these services.

- 2424 -> 192.168.1.100:24 (test PC - SSH)
- 8030 -> 192.168.1.100:8031 (test PC - ufotest web interface)
- 8031 -> ????:80 (network sockets - web interface)
