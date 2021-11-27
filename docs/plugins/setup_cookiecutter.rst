How to setup a new plugin with Cookiecutter
===========================================

To get started with plugin development you really only need the correct folder structure which
you will then have to put into the your :code:`$HOME/.ufotest/plugins` folder.

There is always the possibility of creating this structure on your own, but it is *strongly encouraged*
to use the existing **Cookiecutter** template to set up the initial scaffold.

Installing dependencies
-----------------------

As a first step make sure that cookiecutter is installed:

.. code-block:: console

    python3 -m pip install cookiecutter docutils

Docker-compose can optionally be installed to support the virtual development environment for the
plugin.

.. code-block:: console

    sudo apt-get install docker-compose docker

Downloading the template
------------------------

The best choice is to set up the development repo for this plugin within the plugin folder of an
existing test ufotest installation:

.. code-block:: console

    cd $HOME/.ufotest/plugins
    cookiecutter https://github.com/the16thpythonist/cookiecutter-ufotest-plugin.git

This command will prompt some inputs such as the desired plugin name etc. Afterwards
a new folder should have been created with all the necessary content. We will assume
that this folder is called :code:`example_plugin`.

Development environment
-----------------------

The cookiecutter template supports a docker-compose virtual development environment. What
this means is that a completely blank ufotest instance is created in a docker container
specifically for the purpose of testing that very plugin.

This has the advantage that you do not have to potentially break your existing setup during
development.

To create this development container go into the folder and build the container:

.. code-block:: console
    :caption: in example_plugin

    bash docker/rebuild.sh

After the container was build you can run any ufotest command through the :code:`run.sh` script:

.. code-block:: console
    :caption: in example_plugin

    bash run.sh "ufotest --mock ci serve"

For example starts the web server, which is then also accessible as http://localhost:8030. You should
be able to see your custom plugin listed in the "Plugins" tab.

.. note::

    Obviously the web server will only work if no other ufotest instance is running and no other
    service is already bound to port 8030

Compiling the README
--------------------

The ufotest web interface is able to display the information / documentation of a plugin by using its
:code:`README.html` file. This HTML file does not have to be written separately, instead it can be
automatically generated from the existing :code:`README.rst` file:

.. code-block:: console
    :caption: in example_plugin

    bash doc.sh
    cat README.html


Further Reading
---------------

- https://github.com/cookiecutter/cookiecutter If you are unfamiliar with cookie cutter.
