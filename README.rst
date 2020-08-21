=======
ufotest
=======


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

.. code-block:: console

    $ pip3 install ufotest

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

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
