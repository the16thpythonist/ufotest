"""
Module containing the functions to access the configuration of ufotest.
"""
import os
import toml
from pathlib import Path
from typing import List, Optional

from ufotest.plugin import PluginManager
from ufotest.scripts import ScriptManager

# The path of the this very python package and the path to the default TOML config file, which will be copied during
# the installation of this project
PATH = Path(__file__).parent.absolute()

TEMPLATE_PATH = os.path.join(PATH, 'templates')
STATIC_PATH = os.path.join(PATH, 'static')
CONFIG_TEMPLATE_PATH = os.path.join(TEMPLATE_PATH, 'default.toml')

# This will be the string path to the HOME folder of the user which is currently executing the script
HOME_PATH = str(Path.home())

# This is the default location of the config folder for this project.
# That would be a new hidden folder ".ufotest" within the home folder of the user.
DEFAULT_PATH = os.path.join(HOME_PATH, '.ufotest')

# This string is the name of the environment variable, which can be used to set a different installation path for the
# '.ufotest' folder.
PATH_ENV = 'UFOTEST_PATH'


SCRIPT_DEFINITIONS = [
    {
        'name':             'reset',
        'path':             os.path.join(PATH, 'scripts', 'Reset_all.sh'),
        'class':            'BashScript',
        'description':      'Resets the camera to the default state',
        'author':           'Michele Caselle <michele.caselle@kit.edu>'
    },
    {
        'name':             'reset_tp',
        'path':             os.path.join(PATH, 'scripts', 'Reset_all_TP.sh'),
        'class':            'BashScript',
        'description':      'Resets the camera to the default state, using the Test Pattern configuration',
        'author':           'Michele Caselle <michele.caselle@kit.edu>'
    },
    {
        'name':             'status',
        'path':             os.path.join(PATH, 'scripts', 'status.sh'),
        'class':            'BashScript',
        'description':      'Reads out the internal status parameters of the camera',
        'author':           'Michele Caselle <michele.caselle@kit.edu>'
    },
    {
        'name':             'power_up',
        'path':             os.path.join(PATH, 'scripts', 'PWUp.sh'),
        'class':            'BashScript',
        'description':      'Enables the internal power supply of the camera sensor',
        'author':           'Michele Caselle <michele.caselle@kit.edu>'
    },
    {
        'name':             'power_down',
        'path':             os.path.join(PATH, 'scripts', 'PWDown.sh'),
        'class':            'BashScript',
        'description':      'Disables the internal power supply of the camera sensor',
        'author':           'Michele Caselle <michele.caselle@kit.edu>'
    },
    {
        'name':             'pcie_init',
        'path':             os.path.join(PATH, 'scripts', 'pcie_init.sh'),
        'class':            'BashScript',
        'description':      'Identifies the fpga and initiates the driver for the connection',
        'author':           'Michele Caselle <michele.caselle@kit.edu>'
    },
    {
        'name':             'reset_fpga',
        'path':             os.path.join(PATH, 'scripts', 'reset_fpga.sh'),
        'class':            'BashScript',
        'description':      'Resets the fpga',
        'author':           'Michele Caselle <michele.caselle@kit.edu>'
    },
    {
        'name':             'reset_dma',
        'path':             os.path.join(PATH, 'scripts', 'dma.sh'),
        'class':            'BashScript',
        'description':      'Resets the dma engine of the fpga',
        'author':           'Michele Caselle <michele.caselle@kit.edu>'
    },
    {
        'name':             'hello_world',
        'path':             os.path.join(PATH, 'scripts', 'hello_world.sh'),
        'class':            'BashScript',
        'description':      ('Only echos the single string line "Hello World!". This script does not serve any real '
                             'purpose for the camera. It is only used for testing purposes. With this simple script '
                             'it is possible to test if the scripts are discovered properly and if bash works.'),
        'author':           'Jonas Teufel <jonseb1998@gmail.com>'
    }
]


def get_builds_path() -> str:
    """Returns the string path of the 'builds' folder within the ufotest installation folder.

    :return: the string absolute path of the builds folder
    """
    path = get_path()
    return os.path.join(path, 'builds')


def get_path(*sub_paths) -> str:
    """Returns the path of the installation folder of the ufotest app.

    This installation folder contains for example the following things:
    - The config file for the project. This is a toml file which manages the global config settings for ufotest
    - The 'archive' folder which saves archives of the test reports of all the executed test runs.
    - The 'builds' folder which saves archives of all the reports for the issued builds of the remote source repo.

    :return: the string absolute path to the installation folder
    """
    if PATH_ENV in os.environ.keys():
        return os.path.join(os.environ[PATH_ENV], *sub_paths)
    else:
        return os.path.join(DEFAULT_PATH, *sub_paths)


def get_config_path():
    """
    Returns the path of the config file for ufotest.
    """
    path = get_path()
    return os.path.join(path, 'config.toml')


def load_config():
    """
    Loads the configuration from the config file "config.toml" and returns it as a dictionary
    """
    # First we need to check if a config file even exists.
    # If it does exist, everything is fine and we can load it. If it does not exist at the location
    # were it is supposed to exist we need to create a new one...
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return {}
    else:
        return toml.load(config_path)


def reload_config():
    global CONFIG
    CONFIG = load_config()


class Singleton(type):
    """
    This is metaclass definition, which implements the singleton pattern. The objective is that whatever class uses
    this as a metaclass does not work like a traditional class anymore, where upon calling the constructor a NEW
    instance is returned. This class overwrites the constructor behavior to return the same instance upon calling the
    the constructor. This makes sure that always just a single instance exists in the runtime!

    **USAGE**

    To implement a class as a singleton it simply has to use this class as the metaclass.

    .. code-block:: python

        class MySingleton(metaclass=Singleton):

            def __init__(self):
                # The constructor still works the same, after all it needs to be called ONCE to create the
                # the first and only instance.
                pass

        # All of those actually return the same instance!
        a = MySingleton()
        b = MySingleton()
        c = MySingleton()

        print(a is b) # true
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    """
    This is a singleton class, which implements the access to the config file.

    **DESIGN CHOICE**

    So I feel like I want to explain my reasoning for this class here. This is indeed not my first implementation for
    config access within this project. Previously I was simply loading the dictionary into global variable within this
    file and then I could import this global variable and just use the dictionary.

    But while working with that implementation I have found two major problems with it:

    (1) Reloading: The problem is that the dictionary is loaded into the global variable at exactly the point when
    it is imported the first time at some other module. This means that there is no way of globally reloading the
    config to react to file system changes for example. Even if you were to assign the variable with a new dict
    for example, this change would not translate to other files! The reloaded version would only be present in a single
    file. With a singleton of course you can simply solve this problem with a "reload" method.

    (2) Reacting to change: There is a significant downside to using the config dict directly without some sort of
    intermediary layer. If you need some functionality say "CONFIG['camera']['sensor_height']" then this is the path
    which is directly implemented like this in the config file structure. This means that if you were to change the
    structure of the config file you would have to change every occasion in the code, which uses this attribute...
    This is obviously a bad SOC. With a class you could write methods, which wrap certain behaviour. After a change
    only this method would have to be changed.

    **USAGE**

    In a sense the config singleton instance is the central data structure upon which all the other ufotest
    functionality relies. This instance needs to be accessible by all other code. This is for several reasons. The
    main reason is that this class wraps the access to all the values defined in the ufotest config file. Naturally
    much of the functionality is influenced by the concrete values of these config fields.

    Another reason is because the config singleton also contains the references to the essential plugin manager and
    script manager. The plugin manager is especially important, because it contains the registration of callbacks to
    specific hooks and the instance itself has to be used to invoke a certain hook.

    The config singleton is automatically created whenever this config module is first imported. This is also the point
    at which the config file is being read. So after this point, all the config values themselves can be accessed.
    But the plugin and script manager are NOT yet initialized for this to happen the "prepare" method has to be called
    at the very beginning of the new runtime.

    .. code-block:: python

        import Config from ufotest.config
        # At this point an instance of Config is already loaded and it also contains the values from the actual config
        # file

        # This does not actually create a new instance but returns the only existing one "Config" is a singleton class
        config = Config()
        # Only after this line the plugin manager is actually initialized
        config.prepare()

        # Internally the config instance saves the toml structure as a dict. This is the bad way to access the config
        # values since that structure is subject to change.
        config.data['ci']['hostname']
        # Better use the dedicated wrapper method
        config.get_hostname()

        # The plugin manager is saved as "pm"
        config.pm.do_action('my_custom_action')

        # The script manager is saved as "sm"
        config.sm.invoke('my_script')

    """

    def __init__(self):
        # -- LOAD THE DATA FROM FILE
        self.data = load_config()

        # -- INIT CONTEXT
        # So here is the scenario: I have noticed that I need to pass some parameters from the click command call
        # within the terminal all the way down to the email sending sub routine. This is multiple layers and I totally
        # do not want to modify all of them with an additional parameter.
        # This is why I have come up with the 'context' idea. I'll just have a global object where I save the necessary
        # values in and then I can access them in the email subroutine. And the config object is perfect since this
        # already is a global singleton! I'll just add the additional sub dict "context" which will work exactly as
        # I have intended
        self.data['context'] = {
            'verbose':          False
        }

        self.pm: Optional[PluginManager] = None
        self.sm: Optional[ScriptManager] = None

    def prepare(self) -> None:
        """
        This method needs to be called to properly initialize both the plugin manager and the script manager! Only
        after this method was called the config.sm and config.pm values actually hold references to the manager
        instances.

        :returns: void
        """
        # -- LOADING PLUGINS
        # The plugin manager object maintains the list of all loaded plugins as well as the dictionaries which hold
        # all the callbacks registered to the various hooks. "load_plugins" will search the folder passed to the
        # constructor and interpret every subfolder which contains a main.py file as a plugin. The main.py file will
        # be loaded.
        self.pm = PluginManager(plugin_folder_path=self.get_plugin_folder())
        self.pm.load_plugins()

        # -- LOADING SCRIPTS
        self.sm = ScriptManager(self)
        self.sm.load_scripts()

    def is_prepared(self) -> bool:
        """
        Returns whether or not the plugin and script manager have been initialized

        :returns: Whether or not the plugin and script manager are initialized
        """
        return self.pm is not None and self.sm is not None

    # IMPLEMENTING DICT FUNCTIONALITY
    # -------------------------------

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, item):
        return item in self.data.keys()

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    # == WRAPPER METHODS

    # -- trivial config values --
    # These methods simply return values which are in the config dict anyways. Accessing these values through the single
    # bottleneck of these wrapper methods leaves the option to change the config dict structure in the future without
    # breaking the code in multiple places.

    def verbose(self):
        return self.data['context']['verbose']

    def get_hostname(self):
        return self.data['ci']['hostname']

    def get_port(self):
        return self.data['ci']['port']

    def get_repository_url(self):
        return self.data['general']['repository_url']

    def get_documentation_url(self):
        return self.data['general']['documentation_url']

    def get_archive_path(self):
        return os.path.expandvars(self.data['tests']['archive'])

    def get_date_format(self):
        return self.data['general']['date_format']

    def get_time_format(self):
        return self.data['general']['time_format']

    def get_test_folder(self):
        return self.data['tests']['folder']

    def get_test_suites(self):
        return self.data['tests']['suites']

    def get_ci_repository_url(self):
        return self.data['ci']['repository_url']

    def get_ci_bitfile_path(self):
        return self.data['ci']['bitfile_path']

    def get_ci_branch(self):
        return self.data['ci']['branch']

    def get_ci_suite(self):
        return self.data['ci']['test_suite']

    def get_email_address(self):
        return self.data['ci']['gmail_address']

    def get_email_password(self):
        return self.data['ci']['gmail_password']

    def get_plugin_folder(self):
        return self.data['general']['plugin_folder']

    def get_script_definitions(self):
        return SCRIPT_DEFINITIONS

    def get_path(self) -> str:
        """
        Returns the path of the ufotest installation folder
        """
        return get_path()

    # -- Derived config values --
    # These are the methods which do not simply return the values which are in the config dict anyways, but which also
    # do some processing of the values

    def get_sensor_width(self) -> int:
        """
        Returns the sensor width of the currently selected camera in pixels. Derives this value from the camera
        selection. The config file itself defines multiple different camera profiles. What can be set in the config
        is which profile is active. So this method has to first get the profile to then return the value from the
        according profile section.

        :returns: the int camera width in pixels
        """
        sensor_model = self.data['camera']['model']
        return int(self.data['camera'][sensor_model]['sensor_width'])

    def get_sensor_height(self) -> int:
        """
        Returns the sensor height of the currently selected camera in pixels. Derives this value from the camera
        selection. The config file itself defines multiple different camera profiles. What can be set in the config
        is which profile is active. So this method has to first get the profile to then return the value from the
        according profile section.

        :returns: the int camera height in pixels
        """
        sensor_model = self.data['camera']['model']
        return int(self.data['camera'][sensor_model]['sensor_height'])

    def get_ci_repository_name(self) -> str:
        """
        Returns the string name of the remote repository used for the continuous integration. This name is derived from
        the repo url, which is the only thing saved in the config file
        """
        repository_url = self.get_ci_repository_url()

        # So a URL is basically a path, which means that os.path.basename should give us only the last part of the
        # whole thing. But this part may or may not refer to the repositories .git file, which is why we need to
        # remove that substring.
        repository_name = os.path.basename(repository_url)
        repository_name = repository_name.replace('.git', '')

        return repository_name

    def get_ci_script_definitions(self) -> List[dict]:
        """
        Returns the scripts definitions for the CI repository. This is a list of dicts, where each dict contains
        information about where to find a certain script within the source repository.

        More specifically each of these dicts needs to contain AT LEAST the following fields:

        - name: The unique string name by which the script will be identified within ufotest
        - author: string defining the author name
        - description: A description of the purpose of the script
        - relative_path: A relative path providing the location of the script in question relative to the repo root
        - class: The string class name of a valid implementation of scripts.AbstractScript which defines the type of
          script

        :returns: list of dicts defining scripts within the version controlled source repo
        """
        # The [ci.scripts] section in the config contains each registered script as an individual subsection and the
        # fields of this subsection are the ones which are required as "script_definition". By the nature of toml
        # config files, this section is a dict itself. We only need the list of its values
        script_data = self.data['ci']['scripts']
        return list(script_data.values())

    def get_builds_path(self) -> str:
        """
        Returns the string absolute path to the "builds" folder within the ufotest installation folder. Simply appends
        "builds" to the installation path.
        """
        ufotest_path = self.get_path()
        return os.path.join(ufotest_path, 'builds')

    # == UTILITY METHODS

    def reload(self):
        """
        Reloads the config values from the config file, replacing the current object state with the values read from
        the file.

        :return: void
        """
        # Previously this method just assigned the return value of load_config to the data attribute, but that caused
        # a bug, because the new dict value for data didnt contain the "context" field which is set in the constructor
        # of this class.

        # "load_config" reads the toml config file and returns its content as a dict.
        new_data = load_config()
        self.data.update(new_data)

    def url(self, *paths: str) -> str:
        hostname = self.get_hostname()
        port = self.get_port()

        return '/'.join([
            'http://{}:{}'.format(hostname, port),
            *paths
        ])

    def static(self, name) -> str:
        return self.url('static', name)


# Here we actually create the one and only instance for the config. This is executed ad IMPORT TIME.
CONFIG = Config()
