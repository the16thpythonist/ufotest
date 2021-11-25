Quickstart
==========

It is best to follow the instructions step by step. These are only the most common instructions which assume
you are using a linux operating system and are familiar with the command line.

Installation
------------

Prerequisites: Ufotest is only tested on SUSE and Ubuntu operating systems. It is also assumed that both
:code:`python3>=3.6` and :code:`pip>=19.0.0` are already installed.

Ufotest can be installed directly from PyPi or from Github.

.. note::

    However ufotest is installed, the :code:`--user` flag is absolutely necessary when installing with pip.
    Also avoid installing with :code:`sudo`, or the command line interface may not be accessible

.. code-block:: console

    python3 -m pip install --user ufotest

Note that the PyPi version will not be the most recent version. For development version install from github
instead:

.. code-block:: console

    git clone https://github.com/the16thpythonist/ufotest.git
    cd ufotest
    python3 -m pip install .

To verify a successful installation try the following command:

.. code-block:: console

    ufotest --version

:doc:`Still not working? <../troubleshooting/installation>`

Setup
-----

After the python package has been installed, the actual ufotest installation folder has to be created. On
default this folder will be created as :code:`$HOME/.ufotest`

.. code-block:: console

    ufotest init

You can verify the installation by checking if the config file exists

.. code-block:: console

    cd $HOME/.ufotest
    cat config.toml

Configuration
-------------

The config file is documented and for the most basic usage the options do not have to be changed.
The config file can be edited using a text editor or with this command:

.. code-block::

    ufotest config


Running a test case
-------------------

A test case can be executed using the :code:`ufotest test` command of the command line interface.

Without any connected/configured hardware to test, the :code:`--mock` option can be used to sample a frame
from the mock implementation of the hardware.

.. code-block:: console

    ufotest --mock test frame

A log of this test run can be found in it's own subdirectory within the archive folder. The folders for
each test run are named by the start time of the test.

.. code-block:: console

    cd $HOME/.ufotest/archive
    ls

Web Interface
-------------

The most convenient way to view the test report is by using the web interface. The following command will
start the Flask web server which will serve the interface:

.. code-block:: console

    ufotest --mock ci serve

On default, the server will bind to localhost and can be accessed as http://localhost:8030/
