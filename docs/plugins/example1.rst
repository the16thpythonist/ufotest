Example 1: A hello world plugin
===============================

It is assumed, that the necessary folder structure for the plugin was already setup using the
the :doc:`cookiecutter template <../../plugin/setup_cookiecutter>`.

This document will show an example for a minimalistic plugin, which only has the following
functionality:

- Add a new CLI command which simple prints "Hello World"
- Add a new test case, which simply adds "Hello World" as the test result
- Print "Hello World" before every test run

You can view the full source code for this example at https://github.com/the16thpythonist/hello_world_example

Folder Structure
----------------

This example plugin was created by using the :doc:`cookiecutter template <../../plugin/setup_cookiecutter>`.
The important parts of the folder structure looks like this:

.. code-block::

    + hello_world_example
        + docker
        - __init__.py
        - main.py
        - util.py
        - README.rst
        - README.html
        - run.sh
        - doc.sh

Most of these files will automatically be created by the cookiecutter template. In the following section
we only want to be concerned with the actual python code required to realize the above mentioned functionality

Python Code
-----------

.. code-block:: python
    :caption: util.py


    def print_hello_world():
        print("HELLO WORLD!")


.. note::

    Importing from this :code:`util.py` file from the same plugin folder works! But see below for some quirks
    you have to look out for!


.. code-block:: python
    :caption: main.py

    """
    This text will be the short description of the plugin. The short
    description will for example be displayed in the plugin list view of the web interface.
    Make sure to write a short and concise description of the purpose of the plugin
    the details can then be viewed in the specific README.html
    """
    import sys

    import click

    # Plugins can obviously import from ufotest itself
    from ufotest.hooks import Action, Filter
    from ufotest.testing import AbstractTest, MessageTestResult

    # Since the whole plugin system uses a lot of python dynamic import magic, importing
    # from other modules within the same plugin IS POSSIBLE but has to be done as an
    # absolute import, which uses the plugin name like this:
    from hello_world_example.util import print_hello_world


    # HELLO WORLD BEFORE EACH TEST
    # ============================

    @Action('pre_test', 10)
    def pre_test(test_runner, name):
        print_hello_world()


    # HELLO WORLD COMMAND
    # ===================

    @Filter('plugin_commands', 10)
    def plugin_commands(value, config, context):

        @click.command('hello_world', help='Simply prints hello world')
        def hello_world():
            print_hello_world()

        value['hello_world'] = hello_world
        return value

    # HELLO WORLD TEST CASE
    # =====================

    class HelloWorldTest(AbstractTest):

        name = 'hello_world'
        description = 'Is always correct and has hello world as the result message.'

        def run(self):
            message = 'Hello World'
            exit_code = 0
            return MessageTestResult(exit_code, message)


    @Filter('load_tests', 10)
    def load_tests(value, test_runner):
        # "value" is a dict, where the string key is the unique string name
        # of the test case and the value is the AbstractTest object which
        # actually implements it
        value['hello_world'] = HelloWorldTest

        return value

Only absolute imports
~~~~~~~~~~~~~~~~~~~~~

When importing from another module within the same plugin folder only a absolute specification of this import will
work. This means that the name of the plugin folder has to be used as a prefix for the import.

.. note::

    This may cause an error in your IDE, but the important thing is whether it works in testing. Since the
    plugin systems performs some namespace magic, the IDE may most likely be wrong about this.

Hook Decorators
~~~~~~~~~~~~~~~

As you can see the most common way to register hooks is by using the :code:`Action` and :code:`Filter`
decorators. As the first parameter they expect the string hook name and as the second they *need* an integer
value for the priority.

Test Cases
~~~~~~~~~~

New test cases can be implemented by creating sub classes of the abstract base :code:`AbstractTest`. The only
thing a custom command has to implement is the *run* method. This method has to return an object which implements
:code:`AbstractTestResult`. See the :code:`testing` module for a list of possible test results or implement your own.
Additionally a subclass has to overwrite the static fields for the test name and description.

Further Reading
---------------

- https://click.palletsprojects.com/en/8.0.x/ Since ufotest uses the click library for the command line
  interface, it would make sense to read into this if you are unfamiliar but want to add a custom command
- :doc:`Hook Reference <../hook_reference>` A listing of all the available hooks. Look through them and see
  what might be a good fit for the functionality you have in mind.
