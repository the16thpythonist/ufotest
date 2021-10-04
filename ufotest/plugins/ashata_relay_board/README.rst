Ashata Relay Board - UfoTest Plugin
===================================

This ufotest plugin adds support for the family of "Ashata Relay Boards" of USB controlled and linux compatible relay
boards. The relay boards come with either 2, 4 or 8 separate relay channels. The control over these relay channels
will be exposed to the ufotest system through the *device manager*.

One of the main purposes of using such a relay board is to provide a hard reset for the camera FPGA board. Simply doing
a soft reset by the means of the reset scripts has proven insufficient on some occasions. Cutting the power line will
hard reset the board, which should resolve issues. For further information on how to do this within the ufotest
software, consult the *Usage* section.

Installation
------------

To be able to use the ashata relay board, the linux binary `usbrelay`_ has to be installed on the system.

On ubuntu it can be installed with the system package manager:

.. code-block:: console

    sudo apt-get install usbrelay

To test the installation, try to invoke the command line interface:

.. code-block:: console

    sudo usbrelay --help

.. _usbrelay: https://github.com/darrylb123/usbrelay


Configuration
-------------

The plugin will respect the following configuration options within the main ufotest `config.toml` and otherwise use the
default values for each variable.

.. code-block:: toml

    [ashata_relay_board]

        # When using the command line interface, each ashata board and each COM port on the PC
        # is identified by one such string, which has to be known to use the board properly.
        base_name = "QMZZ"

        # The number of relays on the given board
        relay_count = 4

        # The index of the relay which is used to control the power to the camera module itself.
        camera_index = 1

Usage
-----

The plugin will register a device identified by the string `ashata_relay_board` to ufotest device manager. This device
will mainly contribute the two functions `activate_ashata_relay` and `deactivate_ashata_relay`, which both accept the
index of the target relay as the single argument.

.. code-block:: python

    from ufotest.config import Config

    config = Config()
    config.dm.invoke('activate_ashata_relay', 1)
    config.dm.invoke('activate_ashata_relay', 1)

If the port, with which the camera FPGA board itself is connected, is configured the function `hard_reset_camera` with
no arguments can be used to turn off the camera connection for 1 second and then activate it again.

.. code-block:: python

    config.dm.invoke('hard_reset_camera')
