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

``pre_command_frame``
~~~~~~~~~~~~~~~~~~~~~

Action Hook

kwargs(4):

- config: The instance of the config singleton
- namespace: The dict which represents the namespace of the cli.py module. Modifying this dict with additional values
  allows those new variables to be used within the commands later on.
- output: The string path of where to save the frame
- display: The boolean flag of whether or not to display the frame

This action hook is executed at the very beginning of the code for the "frame" CLI command, but after the generic
``pre_{command}`` hook!

``post_test_context_construction``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Action Hook:

kwargs(2):

- context: The TestContext instance
- namespace: A dict which represents the global namespace of at the end of the TestContext constructor

This action hook is executed as the last thing within the constructor of the TestContext class. Since both the test
context instance itself and the namespace are available. This can be used to attach custom / dynamic attributes to each
test context object, which can then possibly later be used to create custom sections in the test report...


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


``camera_class``
~~~~~~~~~~~~~~~~

Filter Hook

kwargs(1):

- value: The class which is a subclass of camera.AbstractCamera and whose object instance will be invoked to interface
  with the camera.

This filter hook is called in multiple places, whenever a new instance of the camera is supposed to be created. One
example would be the "frame" CLI command, which will request a single frame from the camera object and display it to
the user.

Probably the most important place where this filter is used is within the constructor of testing.TestRunner, where a
new camera instance is created, which will then be passed to every single test case that is scheduled to be run with
that test suite.

This hook will be the most important hook when extending UfoTest to be compatible with a new camera model. Within a
possible plugin, the interfacing with this camera model will have to be implemented as a subclass of
camera.AbstractCamera and then this hook can be used to instruct the core routine to use that class instead of the
default:

.. code-block:: python

    from ufotest.hooks import Filter
    from ufotest.camera import AbstractCamera

    class CustomCamera(AbstractCamera):
        # ...

    @Filter('camera_class', 10)
    def use_custom_camera(value):
        return CustomCamera


Interesting for testing purposes is the fact, that UfoTest comes shipped with an implementation camera.MockCamera,
which does not actually require any hardware but instead only simulates camera behavior. Using this mock implementation
could be enabled like this:

.. code-block:: python

    from ufotest.hooks import Filter
    from ufotest.camera import MockCamera

    @Filter('camera_class', 10)
    def use_mock(value):
        return MockCamera


``get_test_reports``
~~~~~~~~~~~~~~~~~~~~

Filter Hook

kwargs (1):

- value: A list of dicts, where each dict is the dict representation of a test report which was loaded from the
  report.json file within the according report sub folder of the "archive" folder.

This filter filters the return value of the function "util.get_test_reports". The subject value is a list of dicts,
where each dict represents one test report which is saved within the "archive" folder of the ufotest installation.

This hook can for example be used to modify the list of these test reports to exclude certain reports, add additional
ones which are loaded by some external means or simply change the ordering of the reports.


``get_build_reports``
~~~~~~~~~~~~~~~~~~~~~

Filter Hook

kwargs (1):

- value: A list of dicts, where each dict is the dict representation of a build report which was loaded from the
  report.json file within the according report sub folder of the "builds" folder.

This filter filters the return value of the function "util.get_build_reports". The subject value is a list of dicts,
where each dict represents one build report which is saved within the "builds" folder of the ufotest installation.

This hook can for example be used to modify the list of these build reports to exclude certain reports, add additional
ones which are loaded by some external means or simply change the ordering of the reports.

``home_template``
~~~~~~~~~~~~~~~~~

Filter Hook

kwargs: (1):

- value: Jinja template for the home page of the web interface.

This filter applies to the jinja template which is loaded to represent the home page of the web interface. On default
this value will load the template file "home.html" in the templates folder of the ufotest project. This filter allows a
different template to be used, which can be used to implement a fully customized home page.

When implementing a custom home page, it would be best if that custom template *extended* the base "home.html" template
and not replace it entirely. The base home template defines a lot of blocks which can be selectively replaced by a child
template. This should be the preferred method for small changes. For big changes, it is still important to at least
extend the "base.html" template. This base template provides the basic layout for the ufotest web interface, which on
the one hand is the correct import of all stylesheets and JS libraries and on the other hand the basic html
skeleton for the header and footer.

Note that to be able to replace a template one would first have to register the plugin's template folder with the
active jinja environment loader!

The following example shows how to replace the entire content summary box of the home template with a simple hello
world string, but the rest of the page would stay the same:

.. code-block:: html

    <!-- templates/my_home.html -->
    {% extends "home.html" %}

    {% block summary_box %}
        <p>
            Hello World
        </p>
    {% endblock %}

.. code-block:: python

    # main.py
    from ufotest.hooks import Filter
    from ufotest.util import get_template

    from jinja2 import FileSystemLoader

    # This will modify the jinja environment such that it also finds the templates of this plugin
    @Filter("template_loaders", 10)
    def template_loaders(value):
        value.append(FileSystemLoader("/my/plugin/path/templates"))
        return value

    @Filter("home_template", 10)
    def home(value):
        my_home = get_template("my_home.html")
        return my_home

To see the full context dict, which is ultimately passed to the rendering of the home template, see the source code of
the respective function "ufotest.ci.server.home".

``home_recent_count``
~~~~~~~~~~~~~~~~~~~~~

Filter Hook

kwargs (1):

- value: integer

This integer subject value defines how many recent items (test reports and build reports) will be displayed on on the
home page of the web interface.

``home_status_summary``
~~~~~~~~~~~~~~~~~~~~~~~

Filter hook

kwargs (1):

- value: A list of dicts (and boolean) values where each dict element defines one of the values to be displayed in the
  summary box of the home page of the web interface.

This filter allows to modify which (and in which order) values are listed in the "Status Summary" box on the home page
of the web interface. This box is supposed to contain the most important information about the current test setup. A
plugin might have it's own values which are supposed to also be listed in this status summary. This can easily be done
without modifying the whole template by using this hook. The subject value of this hook is a mixed list which consists
of dicts and boolean values (only False to be specific). Each dict represents one value which will be shown in the
status summary, for that the dict needs three fields "id", "label" and "value", where the id will be used as the html
id of the element, label will be the short description before the value and value will be the content of the
span element which actually shows the value.

Furthermore, the list can also contain "False" boolean values. These will be rendered as horizontal separators within
the box. This also implies that the order of the values is important!

An example list would look like this:

.. code-block:: python

    status_summary = [
        {
            'id': 'sensor-temperature',
            'label': 'Sensor Temperature',
            'value': '33.4'
        },
        {
            'id': 'board-temperature',
            'label': 'Board Temperature',
            'value': '43.2'
        },
        False,  # Seperator !
        {
            'id': 'firmware-version',
            'label': 'Firmware Version',
            'value': '1.2.5'
        }
    ]


``template_loaders``
~~~~~~~~~~~~~~~~~~~~

Filter Hook

kwargs (1):

- value: A list of jinja template loaders which are supposed to manage the template loading for the main jinja
  Environment object responsible for the web interface of ufotest.

This filter is absolutely essential if the plugin intends to implement custom jinja template! This filter can be used
to register the plugin specific template folders so that the templates within it can be found. The subject value is a
list of template loaders. On default this list contains only a single loader, which is the main loader for the base
ufotest routine itself. It should only ever be extended! These template loaders will then be passed to a jinja Choice
loader and this is then used as the loader for the central ``TEMPLATE_ENVIRONMENT`` global variable.

A custom template folder can be registered as simply as this:

.. code-block:: python

    # main.py
    from ufotest.hooks import Filter

    from jinja2 import FileSystemLoader


    @Filter("template_loaders", 10)
    def template_loaders(value):
        my_loader = FileSystemLoader("path/to/my/templates")
        value.append(my_loader)
        return value

