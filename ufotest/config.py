"""
Module containing the functions to access the configuration of ufotest.
"""
import os
import toml
import shutil
from pathlib import Path

# The path of the this very python package and the path to the default TOML config file, which will be copied during
# the installation of this project
_PATH = Path(__file__).parent.absolute()
_DEFAULT_CONFIG_PATH = os.path.join(_PATH, 'default.toml')

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
        # Copy the default config file, which comes shipped with this package to the destination where it is
        # supposed to be
        shutil.copy(_DEFAULT_CONFIG_PATH, config_path)

    return toml.load(config_path)


CONFIG = load_config()
