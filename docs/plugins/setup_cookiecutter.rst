How to setup a new plugin with Cookiecutter
===========================================

To get started with plugin development you really only need the correct folder structure which
you will then have to put into the your :code:`$HOME/.ufotest/plugins` folder.

There is always the possibility of creating this structure on your own, but it is *strongly encouraged*
to use the existing **Cookiecutter** template to set up the initial scaffold.

As a first step make sure that cookiecutter is installed

.. code-block:: console

    python3 -m pip install cookiecutter

The best choice is to set up the development repo for this plugin within the plugin folder of an
existing test ufotest installation:

.. code-block:: console

    cd $HOME/.ufotest/plugins
    cookiecutter https://github.com/the16thpythonist/cookiecutter-ufotest-plugin.git

This command will prompt some inputs such as the desired plugin name etc. Afterwards
a new folder should have been created with all the necessary basic

Further Reading
---------------

- https://github.com/cookiecutter/cookiecutter . If you are unfamiliar with cookie cutter.
