The plugin system
=================

The core ufotest software can be extended by adding additional code packages called
*plugins*. This document aims to describe how these external plugins are loaded
and used within this system.

What do plugins look like?
--------------------------

On the fundamental level a ufotest plugin is simply a *folder* which contains python
modules, which in turn contain the custom code.

To be accurately identified as a plugin, these folders have to follow some conventions:

- The *folder name* has to be unique and in snake case. This name will later uniquely
  identify the plugin within the code.
- The folder has to contain an empty :code:`__init__.py` file!
- The folder has to contain a :code:`main.py` file. This file is the entry point for the
  plugin. It may import other modules, but only this main file is executed when the plugin
  is loaded.
- The folder has to contain a :code:`README.rst` file, which acts as the plugins documentation.

An example folder structure may look like this

.. code-block:: text

    my_example_plugin
        + lib
            - util.py
            - functions.py
        - __init__.py
        - main.py
        - README.rst
        - README.html

This folder would be loaded and identified internally by the string name :code:`"my_example_plugin"`.
During the ufotest startup sequence, the :code:`main.py` file would be executed.

Where to put plugins
--------------------

So plugins are merely folders. To be actually loaded, these folders have to be placed in a specific
location.

This location is the *plugins* folder of the ufotest installation, which by default would be:
:code:`$HOME/.ufotest/plugins`.

How plugins are loaded
----------------------

Ufotest has a *plugin* submodule which is responsible for the management of the plugins. At the
core of this system is the :code:`PluginManager` class.

During the startup sequence, this class iterates through the plugins folder and attempts to load
every sub folder which contains a valid main and init module as a plugin.

For each valid plugin folder, the contents of the main.py file are executed. Usually this includes
the registration of so called *hooks* within the plugin manager. The custom logic registered with
these so called hooks is then executed at various points throughout the main runtime, which
induces the desired plugin functionality.

Further reading
---------------

- :doc:`../hook_system.rst`: An explanation of the hook system, which allows the plugins to inject
  custom code into the main runtime.

