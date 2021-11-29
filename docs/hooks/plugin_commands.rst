``plugin_commands`` - Filter
-----------------------------

------------

Keyword Arguments
~~~~~~~~~~~~~~~~~

value: dict
    A dictionary whose string keys are the unique CLI command names and the values are the :code:`click.Command`
    objects which implement the corresponding cli command.

config: Config
    A reference to the main config instance at that point of the runtime

context:
    The click context object


Description
~~~~~~~~~~~

It is possible for a plugin to add custom commands to the ufotest CLI by using this filter hook. Although for
technical reasons it is not possible to add *top layer* commands. It is only possible to add these plugin specific
commands to a command subgroup called :code:`plugin`, which would then be invoked like this:

.. code-block:: console

    ufotest plugin {custom_command}

But other than that, additional layers of nesting are possible. Instead of a singular command, one could also add
another command group to this :code:`plugin` group.

The core data :code:`value` for this filter hook is a dict, whose string keys are the names the commands and the
values are the :code:`click.Command` objects, which are usually obtained by simply decorating a python function
accordingly.

Additionally the hook receives a reference to the config instance and the command context. This command context
can be used to get information about the command line options etc. For more info see the click documentation.

Example
~~~~~~~

Adding a new command:

.. code-block:: python

    import click
    from ufotest.hooks import Filter

    # The actual command function
    @click.command('hello_world', help='Simply prints hello world')
    def hello_world():
        print('Hello World!')

    # Register the hook
    @Filter('plugin_commands', 10)
    def plugin_commands(value, config, context)
        value['hello_world'] = hello_world
        return value

This command could then be invoked like this:

.. code-block:: console

    ufotest plugin hello_world

