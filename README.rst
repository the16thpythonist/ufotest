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
Institute of Data Processing (IPE) of the Karlsruhe Institute of Technology (KIT).

* Free software: MIT license
* Documentation: https://ufotest.readthedocs.io.

Installation
------------

The easiest way to install this package is by using PIP. This will automatically install all the requirements and
also register the CLI commands to be usable.
(Note that the "sudo" is important to make the commands register correctly within the operating system)

.. code-block:: console

    $ pip3 install --user ufotest
    $ export PATH=$PATH:$HOME/.local/bin
    $ ufotest init

Usage
-----

The command line can be accessed through the `ufotest` command within the console. Use the `--help` option to display
a list of all available commands or consilt the Documentation for a more detailed explanation

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

* Flask_: Python microframework for creating web applications with minimal effort
* Click_: Python library for creating CLI applications
* Jinja2_: Templating library for Python
* Cookiecutter_: A CLI tool for project templating
* `audreyr/cookiecutter-pypackage`_: A basic template for python package projects

.. _Flask: https://github.com/pallets/flask
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _Click: https://click.palletsprojects.com/en/7.x/
.. _Jinja2: https://jinja.palletsprojects.com/en/2.11.x/


ToDo
----

- [] Fix the crashes during the build process. No error should cause the program to crash
- [] Fix the crash whenever a git repository url is formatted incorrectly
- [] Document the current setup within the documentation
- [] Automatic generation of a datasheet with the camera properties (as a single test case?)
- [] Redesign the loading of tests cases so that positional parameters can be encoded in the name
- [] Make the server process automatically start on boot for the test PC in the DAQ lab
- [] Test case for x number of executions of the setup script. How many were successful?
- [] Test case for x number of frame acquisitions. How many were successful?
