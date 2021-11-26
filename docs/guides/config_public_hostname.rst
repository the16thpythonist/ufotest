How to configure web server with a public hostname
==================================================

The :doc:`Quickstart Guide <../../quickstart>` shows how to start the Flask web server which serves the
web interface. On default this server runs on :code:`localhost`, but it is also possible to make the
interface publicly accessible.

**Prerequisite:** It is assumed that your machine already has a public IP address and a public hostname
associated with it, which we will be calling :code:`ufotest.example.com`.

Setting the hostname in the config
----------------------------------

This hostname has to be specified in the ufotest config file. Navigate to the installation folder or
use the command to edit the config file:

.. code-block:: console

    ufotest config

In the :code:`[ci]` section change the following line:

.. code-block:: toml
    :caption: config.toml

    [ci]
        hostname = 'ufotest.example.com'

Changing the port
-----------------

The default port for ufotest is **8030**. So after changing the hostname, the server would be accessible
as http://ufotest.example.com:8030/ . It is encouraged to stay with this configuration.

If this is not possible due to a firewall etc, change the port like this in the config file:

.. code-block:: toml
    :caption: config.toml

    [ci]
        hostname = 'ufotest.example.com'
        port = 80
