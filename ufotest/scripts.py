import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import click

from ufotest.config import CONFIG


PATH = Path(__file__).parent.absolute()
SCRIPTS_PATH = os.path.join(PATH, 'scripts')


SCRIPT_AUTHORS = {
    'michele':              'Michele Caselle <michele.caselle@kit.edu>',
    'jonas':                'Jonas Teufel <jonseb1998@gmail.com',
    'timo':                 'Timo Dritschler <timo.dritschler@kit.edu>'
}


class AbstractScript(object):

    def __init__(self, script_definition: Dict[str, Any]):
        self.data = script_definition

    def invoke(self, args: Optional[Any] = None):
        pass


class BashScript(AbstractScript):

    def __init__(self):
        pass


class ScriptManager(object):

    # DESIGN DECISION
    # Explicitly pass in all relevant parameters?
    # + More separation of concerns
    # + Dependencies are more transparent
    # Pass in the config instance?
    # + In the future this class might need access to more config values and then I would not need to change the
    #   the constructor signature
    # + It is more unified, since all the other "manager" classes also just use the config.
    # + definitely easier
    # - I cannot actually import the config class since that would cause circular dependency.
    def __init__(self, config):
        self.config = config
        self.config.pm.do_action('script_manager_pre_construct', self.config)

        self.fallback_script_definitions: List[dict] = self.config.get_script_definitions()
        self.fallback_script_definitions = self.config.pm.apply_filters(
            'fallback_script_definitions',
            self.fallback_script_definitions
        )
        self.fallback_scripts = {}

    def load_fallback_scripts(self):
        for script_definition in self.fallback_script_definitions:
            script_name = script_definition['name']
            script_class = eval(script_definition['class'])
            self.fallback_scripts[script_name] = script_class(script_definition)

    def load_scripts(self):
        pass


SCRIPTS = {
    'reset': {
        'path':             os.path.join(SCRIPTS_PATH, 'Reset_all.sh'),
        'description':      'Resets the camera parameters to the default state',
        'author':           SCRIPT_AUTHORS['michele']
    },
    'reset_tp': {
        'path':             os.path.join(SCRIPTS_PATH, 'Reset_all_TP.sh'),
        'description':      'Resets the camera parameters to the default state and activates the test pattern',
        'author':           SCRIPT_AUTHORS['michele']
    },
    'status': {
        'path':             os.path.join(SCRIPTS_PATH, 'status.sh'),
        'description':      'Reads out the status parameters of the camera',
        'author':           SCRIPT_AUTHORS['michele']
    },
    'power_up': {
        'path':             os.path.join(SCRIPTS_PATH, 'PWUp.sh'),
        'description':      'Enables the internal power supply of the camera sensor',
        'author':           SCRIPT_AUTHORS['michele']
    },
    'power_down': {
        'path':             os.path.join(SCRIPTS_PATH, 'PWDown.sh'),
        'description':      'Disables the internal power supply of the camera sensor',
        'author':           SCRIPT_AUTHORS['michele']
    },
    'pcie_init': {
        'path':             os.path.join(SCRIPTS_PATH, 'pcie_init.sh'),
        'description':      'Identifies the fpga and initiates the driver for the connection',
        'author':           SCRIPT_AUTHORS['michele']
    },
    'reset_fpga': {
        'path':             os.path.join(SCRIPTS_PATH, 'reset_fpga.sh'),
        'description':      'Resets the fpga',
        'author':           SCRIPT_AUTHORS['michele']
    },
    'reset_dma': {
        'path':             os.path.join(SCRIPTS_PATH, 'dma.sh'),
        'description':      'Resets the dma engine of the fpga',
        'author':           SCRIPT_AUTHORS['michele']
    }
}

# Dynamically registering the scripts from the config file also.
if 'scripts' in CONFIG.keys():
    SCRIPTS.update(CONFIG['scripts'])


