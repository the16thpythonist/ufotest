Interaction with the Hardware
=============================

Ufotest aims to be a continuous testing framework for hardware devices, which can somehow be connected or
be interacted with by an additional PC. The main consideration for this scenario is that the individual
realisation of what kind of hardware this could be can vary greatly.

Because of this, ufotest aims not to include explicit code to interact with the hardware, instead it relies
on the assumption that a potential user already has a database of programs and scripts to interact with
the individual hardware. These scripts merely have to be (made) callable by the ufotest system to
facilitate an interaction.

The *scripts* system
--------------------

For this purpose, ufotest implements the so called *scripts* system. This is a submodule of ufotest which
manages these third party scripts with which the hardware can be accessed.

At the core of this system is the :code:`ScriptManager` class, which is initialized as part of the startup
sequence of any ufotest command. During this startup sequence the ScriptManager loads all the third party
scripts, after they have been loaded, these scripts can be invoked through the ScriptManager, which is part
of the config singleton (which is accessible from within the whole codebase, which also includes the test cases)

Register custom scripts
-----------------------

The main point of having this script system is that different custom scripts can be registered for each
individual use case. There are mainly ways how this is done.

- *Via a custom plugin.* This is because the design guideline is, that each new individual hardware has to
  be implemented as a custom plugin. For detailed information on how to get stared with such a custom plugin
  see the Plugin Development Guide.
- *Dynamically from the source repository.* These scripts which facilitate the hardware interaction may
  themselves be subject to version control. They may be part of the remote repository which is the anchor
  point for the automatic builds and for each new build, these remote versions will be used instead.

Further Reading
---------------



