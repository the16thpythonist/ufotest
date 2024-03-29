=======
ufotest
=======

.. image:: https://raw.githubusercontent.com/the16thpythonist/ufotest/master/logo.png
        :target: https://pypi.python.org/pypi/ufotest
        :alt: Logo

.. image:: https://img.shields.io/pypi/v/ufotest.svg
        :target: https://pypi.python.org/pypi/ufotest

.. image:: https://img.shields.io/travis/the16thpythonist/ufotest.svg
        :target: https://travis-ci.com/the16thpythonist/ufotest

.. image:: https://readthedocs.org/projects/ufotest/badge/?version=latest
        :target: https://ufotest.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


The ufotest project provides a command line interface to install and test the UFO camera, which was developed at the
`Institute of Data Processing (IPE) <https://www.ipe.kit.edu/>`_ of the
`Karlsruhe Institute of Technology (KIT) <https://www.kit.edu/>`_.

* Free software: MIT license
* Documentation: https://ufotest.readthedocs.io

Installation
============

The easiest way to install this package is by using PIP. This will automatically install all the requirements and
also register the CLI commands to be usable.

.. code-block:: console

    pip3 install --user ufotest
    export PATH=$PATH:$HOME/.local/bin

The :code:`init` command initializes the installation folder for the application which is needed for the functionality
of the other commands.

.. code-block:: console

    ufotest init

Usage
=====

The command line can be accessed through the :code:`ufotest` command within the console. Use the
:code:`--help` option to display
a list of all available commands or consult the `Documentation <https://ufotest.readthedocs.io>`_ for a more detailed explanation

.. code-block:: console

    ufotest --help

Installing all dependencies
---------------------------

To operate the ufo camera with on a new machine, several system packages and dependencies in the form of C code
repositories have to be installed on the system. To simplify this setup process, the ufotest CLI offers the
``install-all`` command:

.. code-block:: console

    ufotest install-all .

.. note::

    Be sure to configure the correct operating system, camera dimensions etc in the ufotest config file by using the
    ``ufotest config`` command first.

Installing single dependency
----------------------------

To install only a single dependency such as the "pcitool" repository, use the ``install`` command:

.. code-block::

    ufotest install "pcitool" .

The ``--save-json`` flag can be used to create a "install.json" report file, which contains information about the
installation process:

.. code-block:: console

    ufotest install --save-json "pcitool" .
    cat install.json


Display single frame
--------------------

A single frame can be displayed by using the ``frame`` command. For testing purposes it is encouraged to also use the
``--mock`` option for the base command. This will use the mock implementation of the camera interface and for the frame
command specifically just display a static picture. Without the mock option, the default interface would be the
UfoCamera implementation which would require a functional HiFlex FPGA board with UFO sensor to be installed in the PC.

.. code-block:: console

    ufotest --mock frame --display


Starting the web interface
--------------------------

The web interface can be started using the ``serve`` command from the ``ci`` command subgroup.

.. code-block:: console

    ufotest --mock ci serve

This will create a Flask web server on the default port **8030** of the local machine, which can be viewed with a
web browser at ``http://localhost:8030``. The web interface can be used for the following tasks:

- View a status summary of all the most important info on the home page
- edit the config file
- View all archived test and build reports

Development
===========

Setup of development environment
--------------------------------

First clone this repository into a local folder using ``git``:

.. code-block:: console

    git clone https://github.com/the16thpythonist/ufotest.git

Then install all the requirements and the dev requirements using ``pip``:

.. code-block:: console

    cd ufotest
    pip3 install -r requirements.txt
    pip3 install -r requirements_dev.txt

To then install the ufotest program, including the command line interface, from your local
development version, run in the ufotest folder:

.. code-block:: console

    pip3 install .

SCSS preprocessor
~~~~~~~~~~~~~~~~~

Since version 2.0.0, the web interface is developed using the SASS CSS preprocessor. To make changes to these style
templates, ``sass`` should be installed on the system:

.. code-block:: console

    npm install -g sass


Using ``local.sh``
~~~~~~~~~~~~~~~~~~

In the root folder of the ufotest repository, there is a utility bash script called ``local.sh`` This script will
perform the following routine actions to install the local changes:

- Compile all SCSS templates for the web interface
- Use pip to install the new version of the code locally
- run ``ufotest init --update`` to copy new static assets into the installation folder
- Start the web interface server

.. code-block:: console

    bash local.sh

Testing
-------

The unittests of the ufotest program are located in the *tests* folder in the top level repository
folder. To run these tests, `pytest <https://docs.pytest.org/en/6.2.x/>`_ is required. This should have
been installed by the *requirements_dev.txt* file. You can check the installation by running

.. code-block:: console

    pytest --version

If pytest is successfully installed, the unittests for ufotest can be executed by running in the repository
root folder:

.. code-block:: console

    make test


Pushing a new version
---------------------

To push a new version to the python package repository PyPI, first write up the changes in the *HISTORY.rst* file.

Then change the content of the *VERSION* file of the top level repository to the new version string. Make sure that
there are no additional whitespaces, newline or tab characters in that file.

Finally run the following code, which will first install the new version on the local system and then create the
distribution files which are pushed to pypi using
`twine <https://pypi.org/project/twine/>`_:

.. code-block:: console

    make install
    make dist

This will prompt the credentials for PyPi.org. Finally the new version can be verified locally:

.. code-block:: console

    ufotest --version

Features
========

- Global configuration file
- Automatic installation of all dependencies for a barebones operation of the UFO camera
- Frame acquisition and display with matplotlib
- Dynamic discovery of custom camera test cases
- Automatic generation of test reports
- standalone CI server which accepts github push event webhooks and automatically starts a new build from the remote
  repo to then execute a test suite
- Wordpress like plugin system using action and filter hooks to extend the base system

Credits
-------

The following software was used in the creation of the project:

* `Flask <https://github.com/pallets/flask>`_: Python microframework for creating web applications with minimal effort
* `Click <https://click.palletsprojects.com/en/7.x/>`_: Python library for creating CLI applications
* `Jinja2 <https://jinja.palletsprojects.com/en/2.11.x/>`_: Templating library for Python
* `Cookiecutter <https://github.com/audreyr/cookiecutter>`_: A CLI tool for project templating
* `audreyr/cookiecutter-pypackage <https://github.com/audreyr/cookiecutter-pypackage>`_: A basic template for python package projects
* `Twine <https://pypi.org/project/twine/>`_: For pushing new versions of the code to the python package index PyPi
* `CodeMirror: <https://codemirror.net/>`_: JS library for displaying a code editor widget.
* `FontAwesome: <https://https://fontawesome.com/>`_: CSS/JS Icon library.

ToDo
----

- [ ] Integrate a dockerfile which will create a container environment in which to run ufotest for development/tests
- [x] Fix the crashes during the build process. No error should cause the program to crash
- [x] Fix the crash when terminating the "serve" command
- [ ] Fix the crash whenever a git repository url is formatted incorrectly
- [x] Document the current setup within the documentation
- [ ] Automatic generation of a datasheet with the camera properties (as a single test case?)
- [ ] Redesign the loading of tests cases so that positional parameters can be encoded in the name
- [x] Make the server process automatically start on boot for the test PC in the DAQ lab
- [x] Test case for x number of executions of the setup script. How many were successful?
- [x] Test case for x number of frame acquisitions. How many were successful?
- [x] Make all commands have a valid return code
- [ ] Installation functions refactor to use the new "run_command" and new verbosity system
- [x] Fix the ugly error message of the frame command
- [ ] Add a '--png' option or smth. to the frame command, where the image is automatically converted to png
