Plugin Development Guide
========================

**Prerequisites:**

- :doc:`../../concepts/plugin_system`. It would be beneficial to know how the plugin
  system was designed from a theoretical perspective.
- :doc:`../../concepts/hook_system`. Same goes for the design choices regarding the
  hook system.

This document references the resources to get started with developing a custom
ufotest plugin. It would make sense to look at each of the sections in the order
presented.

First of all, *why even bother with plugins?*. There are two main reasons

- Using the ufotest system for any custom hardware has to be done by implementing
  one such plugin for the hardware. Within this plugin it has to be implemented
  how to interact with the hardware and which test cases to execute.
- Plugins can also be used to extend the functionality of the core system. This could
  be anything from changing the web interface style to adding new commands to the CLI
  and creating a REST API.

At the end of the guide there are simple examples which show mock plugin implementations
which may act as a starting point for your own plugin.

.. toctree::
    :maxdepth: 1

    plugins/setup_cookiecutter
    plugins/example1



