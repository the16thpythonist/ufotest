Plugin Hook Specifications
==========================

Filter Hooks
------------

``script_manager_pre_construct``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

args (1): script_manager

This action hook gets executed at the very beginning of the scripts.ScriptManager constructor. It accepts a single
argument which is the "self" instance of the script manager. It would be possible to dynamically attach additional
attributes to the script manager for example.

One trick you could be doing here is to define custom script classes (subclass implementations of AbstractScript)
here and attach them to as attributes to the script manager. These custom script classes could then be used in the
script definitions:

.. code-block:: python

    class MyScript(AbstractScript):

        # ...

    @Action('script_manager_pre_construct')
    def register_my_script(self):
        self.MyScript = MyScript

    # And later with the fallback definitions
    @Filter('fallback_script_definitions')
    def add_scripts(script_definitions):
        script_definitions.append({
            'name': 'fully_custom'
            # This will work since the class string here is piped into an "eval" within a method of the script
            # manager
            'class': 'self.MyScript'
            # ...
        })

``fallback_script_definitions``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

args(1): fallback_script_definitions

This filter hook gets triggered in the constructor of the script manager, its outcome specifies the value of the
internal attribute *fallback_script_definitions*. This is a list with dict values. Each dict value
registers a fallback script in the ufotest system. A fallback script is a version of a camera interaction script which
is shipped with the ufotest software itself and which is used when no remote build has been triggered yet or if the
remote build fails. Each dict value has to contain at least the following information:

- name: The string name identifier for the script, which will be used to invoke the script from within the ufotest code
- path: The absolute string path to the script
- class: The string class name of a subclass of "scripts.AbstractScript" which will be used to represent the script.
  this will also define how the script is invoked etc.
- description: A string description of what the script does
- author: A string defining the author of the script

An example would be the following:

.. code-block:: python

    fallback_script_definitions = [
        {
            'name': 'hello',
            'path': '/path/to/custom/script.sh',
            'class': 'BashScript',
            'description': 'echos hello world',
            'author': 'Jonas Teufel <jonseb1998@gmail.com>'
        }
    ]

Use this hook to manipulate which scripts are known and usable by the ufotest system.
