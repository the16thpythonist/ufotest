import os
from pathlib import Path

import click

from ufotest.config import CONFIG


PATH = Path(__file__).parent.absolute()
SCRIPTS_PATH = os.path.join(PATH, 'scripts')


SCRIPT_AUTHORS = {
    'michele':              'Michele Caselle <michele.caselle@kit.edu>',
    'jonas':                'Jonas Teufel <jonseb1998@gmail.com',
    'timo':                 'Timo Dritschler <timo.dritschler@kit.edu>'
}


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


