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
------------

The easiest way to install this package is by using PIP. This will automatically install all the requirements and
also register the CLI commands to be usable.

.. code-block:: console

    $ pip3 install --user ufotest
    $ export PATH=$PATH:$HOME/.local/bin

The :code:`init` command initializes the installation folder for the application which is needed for the functionality
of the other commands.

.. code-block:: console

    $ ufotest init

Usage
-----

The command line can be accessed through the :code:`ufotest` command within the console. Use the
:code:`--help` option to display
a list of all available commands or consult the `Documentation <https://ufotest.readthedocs.io>`_ for a more detailed explanation

.. code-block:: console

    $ ufotest --help

Features
--------

- Global configuration file
- Automatic installation of all dependencies for a barebones operation of the UFO camera
- Frame acquisition and display with matplotlib
- Dynamic discovery of custom camera test cases
- Automatic generation of test reports
- standalone CI server which accepts github push event webhooks and automatically starts a new build from the remote
  repo to then execute a test suite

Credits
-------

The following software was used in the creation of the project:

* `Flask <https://github.com/pallets/flask>`_: Python microframework for creating web applications with minimal effort
* `Click <https://click.palletsprojects.com/en/7.x/>`_: Python library for creating CLI applications
* `Jinja2 <https://jinja.palletsprojects.com/en/2.11.x/>`_: Templating library for Python
* `Cookiecutter <https://github.com/audreyr/cookiecutter>`_: A CLI tool for project templating
* `audreyr/cookiecutter-pypackage <https://github.com/audreyr/cookiecutter-pypackage>`_: A basic template for python package projects


ToDo
----

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
