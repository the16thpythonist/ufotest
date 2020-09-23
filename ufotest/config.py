"""
Module containing the functions to access the configuration of ufotest.
"""
import os
import toml
from pathlib import Path

import shutil
from jinja2 import Environment, PackageLoader, select_autoescape

# The path of the this very python package and the path to the default TOML config file, which will be copied during
# the installation of this project
PATH = Path(__file__).parent.absolute()

TEMPLATE_PATH = os.path.join(PATH, 'templates')
CONFIG_TEMPLATE_PATH = os.path.join(TEMPLATE_PATH, 'default.toml')

# This will be the string path to the HOME folder of the user which is currently executing the script
HOME_PATH = str(Path.home())

# This is the default location of the config folder for this project.
# That would be a new hidden folder ".ufotest" within the home folder of the user.
DEFAULT_PATH = os.path.join(HOME_PATH, '.ufotest')

# This string is the name of the environment variable, which can be used to set a different installation path for the
# '.ufotest' folder.
PATH_ENV = 'UFOTEST_PATH'


def get_path():
    """
    Returns the path of the folder, where all the global persistent assets of ufotest are being stored.
    """
    if PATH_ENV in os.environ.keys():
        return os.environ[PATH_ENV]
    else:
        return DEFAULT_PATH


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

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    """
    This is a singleton class, which implements the access to the config file.

    **Design Choice**

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
    """

    def __init__(self):
        self.data = load_config()

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

    # WRAPPER METHODS
    # ---------------

    def get_sensor_width(self):
        sensor_model = self.data['camera']['model']
        return self.data['camera'][sensor_model]['sensor_width']

    def get_sensor_height(self):
        sensor_model = self.data['camera']['model']
        return self.data['camera'][sensor_model]['sensor_height']

    def get_archive_path(self):
        return os.path.expandvars(self.data['tests']['archive'])

    def get_date_format(self):
        return self.data['general']['date_format']

    def get_time_format(self):
        return self.data['general']['time_format']

    # UTILITY METHODS
    # ---------------

    def reload(self):
        self.data = load_config()


CONFIG = Config()
