Plugin Hook Specifications
==========================

This section lists the explanations for all available hooks. Hooks are identified by their string names. They are part
of the plugin system and enable custom code from plugins to be executed at certain points within the core ufotest
routines. There is generally a distinction between *action* and *filter* hooks. Action hooks do not have a return value
and they only exist so that some custom code can be executed at a specific point in the core routine. Filter hooks
accepts a special "value" argument which ultimately has to be returned again. They provide the possibility of
modifying certain core data structures.


Action Hooks
------------

``script_manager_pre_construct``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Action Hook

kwargs (2):

- sm: A reference to the script manager instance itself. But keep in mind that since this hook is invoked at the
  earliest point in the constructor, none of the attributes exist yet.
- namespace: A dict, which defines the global namespace within the scripts module.

This action hook gets executed at the very beginning of the scripts.ScriptManager constructor. It accepts a single
argument which is the "self" instance of the script manager. It would be possible to dynamically attach additional
attributes to the script manager for example.

One trick you could be doing here is to define custom script classes (subclass implementations of AbstractScript)
here and attach them to the namespace. These custom script classes could then be used in the
script definitions:

.. code-block:: python

    class MyScript(AbstractScript):

        # ...

    @Action('script_manager_pre_construct')
    def register_my_script(sm, namespace):
        namespace["MyScript"] = MyScript

    # And later with the fallback definitions
    @Filter('fallback_script_definitions')
    def add_scripts(script_definitions):
        script_definitions.append({
            'name': 'fully_custom'
            # This will work since the class string here is piped into an "eval" within a method of the script
            # manager
            'class': 'MyScript'
            # ...
        })


``pre_command``
~~~~~~~~~~~~~~~

Action Hook

kwargs(3):

- config: The instance of the config singleton
- namespace: The dict which represents the namespace of the cli.py module. Modifying this dict with additional values
  allows those new variables to be used within the commands later on.
- context: This is the click Context object, which contains all the information about the actual command call. This
  includes the information about which sub command was invoked and which parameters have been passed.

This action is actually executed *directly* after calling "Config.prepare" which means after the plugins have been
loaded etc. This is probably the earliest available hook to execute some generic setup steps within the runtime of any
individual command.


Filter Hooks
------------


``fallback_script_definitions``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Filter Hook

kwargs(1):

- script_definitions: A list of dicts, where each dict describes one script to be registered

returns: script_definitions

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

``build_script_definitions``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Filter Hook

kwargs(1):

- script_definitions: A list of dicts, where each dict describes one script to be registered

returns: script_definitions

This filter hook gets triggered in the constructor of the script manager, its outcome specifies the value of the
internal attribute *build_script_definitions*. This is a list with dict values. Each dict value
registers a build script in the ufotest system. Build script definitions define how to extract the scripts from the
remote repository (which are cloned for continuous integration builds). Each dict has to have at least the following
fields (potentially more depending on the specific script class):

- name: The string name identifier for the script, which will be used to invoke the script from within the ufotest code
- relative_path: A relative path string. This path is supposed to define the position of the corresponding script file
  relative to the root folder of the remote repository. When loading the scripts within ufotest for any given CI build
  these relative paths will be used to construct the absolute paths automatically in combination with the information
  about the path of the local clone of the repo.
- class: The string class name of a subclass of "scripts.AbstractScript" which will be used to represent the script.
  this will also define how the script is invoked etc.
- description: A string description of what the script does
- author: A string defining the author of the script


``ufo_camera_tmp_path``
~~~~~~~~~~~~~~~~~~~~~~~

Filter Hook

kwargs(1):

- value: The string absolute path of the folder where the ufo camera should store the temporary files

returns: value

The UfoCamera class interfaces with the camera. For acquiring frames, it is necessary to create two temporary files
which store the raw received bytes and the .raw format of the image. On default the folder for storing these is set as
/tmp. This can be changed with this hook


``get_version``
~~~~~~~~~~~~~~~

Filter Hook

kwargs(1):

- value: The version string which was already loaded from the VERSION file and sanitized for additional whitespaces
  and newlines.

The ufotest python package (Not the installation folder!) ships a file called VERSION, which only contains the string
representation of the current version. This content of this file can be read from within the code and the version
string can be used. This filter is able to modify this version before it is returned by the central utility function
"get_version".
