The Hooks System for Plugins
============================

The *plugin system* is responsible for discovering the plugin folders and then
executing their respective :code:`main.py` modules. The question which remains is
how the execution of these modules actually inserts new functionality into the runtime.
How do plugins actually add new features?

The primary thing which is done within those plugin files is the registration
of so called *hook callbacks*. The term hook thereby refers to the fact, that at
various points within the main ufotest codebase there are certain *anchor points*
which expose themselves for custom code to latch onto.

The ufotest hook system is strongly inspired by the Wordpress hook system and thus
hooks come in two flavors:

- **Action hooks**. The anchors for these hooks can be defined at various points within
  the code as functions *without* a return value. They simply get executed and thereby
  provide the option for custom code to be executed at a certain time in the runtime.
  A simple example for this would be an anchor which is invoked every time right before
  a test case gets executed. As a hook callback a plugin could simply add a print statement
  which notifies the execution of a test case in the console.
- **Filter hooks**. These are functions which get passed a certain main data structure
  as a parameter and then return this very same data structure again, optionally with some
  custom modifications. A simple example for such a data structure would be the list of all
  the test cases available to the system. Custom plugin code could modify this list by adding
  some custom test cases, which would then be available to the user.

Action Hooks
------------

The principle is most easily explained for action hooks. Consider the following example:

.. code-block:: python
    :caption: Mock example of an action hook

    # Somewhere in plugin "main.py" during startup sequence
    plugin_manager.register_action("custom_action", lambda: print('Hello World'))

    # ...
    # Later in main runtime
    plugin_manager.do_action("custom_action")
    # prints "Hello World"


Within the plugin main file, a callback (a function / callable object) is registered with the
plugin manager. This callable object is then saved in a list associated with the unique name of
the hook.

Later on during the runtime, the plugin manager is queried with this exact unique hook name. All
the previously registered callables are retrieved and *only then* actually executed. Thus the
custom function from the plugin is called somewhere during the main runtime.

Filter Hooks
------------

Filter hooks function in the same way, in that custom callable objects are registered in a list
associated with some unique hook name. Then somewhere later in the code this hook is actually invoked
to execute these custom functions.

The difference with *filter* hooks is that their purpose is to modify a data structure. They get
this data structure as a parameter and have to return it again.

.. code-block:: python
    :caption: Mock example of a filter hook

    # Somewhere in plugin "main.py" during startup sequence
    def append_one(l):
        l.append(1)
        return l

    plugin_manager.register_action("custom_filter", append_one)

    # ...
    # Later in main runtime
    l = [2, 3, 0]
    l = plugin_manager.apply_filter("custom_filter", l)
    # Result: l = [2, 3, 0, 1]

Multiple callbacks for the same hook
------------------------------------

It is possible to register multiple callbacks for the same hook. Each unique hook name is associated
with a list which may store registered callbacks. Usually this list will be empty and invoking the hook
wont do anything. There may only be one function in the list, but there can also be multiple.

For multiple callbacks they are executed in a sequence. For this plugin system it is also possible to
provide a integer number for the priority. This priority is then used to determine the order of execution.

The possibility of multiple callbacks is especially important for the filter hooks. Multiple callbacks
create a processing pipeline for the subject data structure.

.. code-block:: python
    :caption: Mock example of multiple filter hooks

    # Somewhere in plugin "main.py" during startup sequence
    def append_one(l):
        l.append(1)
        return l

    # Register the same function twice with different priorities
    plugin_manager.register_action("custom_filter", append_one, 10)
    plugin_manager.register_action("custom_filter", append_one, 12)

    # ...
    # Later in main runtime
    l = [2, 3, 0]
    l = plugin_manager.apply_filter("custom_filter", l)
    # Result: l = [2, 3, 0, 1, 1] -> two additional ones!
