import os
import toml
import shutil
from pathlib import Path

_PATH = Path(__file__).parent.absolute()
_DEFAULT_CONFIG_PATH = os.path.join(_PATH, 'default.toml')

HOME_PATH = str(Path.home())
DEFAULT_PATH = os.path.join(HOME_PATH, '.ufotest')

PATH_ENV = 'UFOTEST_PATH'


def get_path():
    if PATH_ENV in os.environ.keys():
        return os.environ[PATH_ENV]
    else:
        return DEFAULT_PATH


def get_config_path():
    path = get_path()
    return os.path.join(path, 'config.toml')


def load_config():
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
print("Hello from Config!")
