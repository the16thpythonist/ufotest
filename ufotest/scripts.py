import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from abc import abstractmethod

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
    """
    The abstract base class for representing scripts.

    The script manager loads knowledge about external scripts based on a dict representation providing important
    information about that script. But this is only the most convenient human readable representation of the script
    knowledge. During the loading process, this dict information is converted into a script wrapper object. These
    have to be specific sub classes of this base class. Each specific implementation of this base class represents
    a different kind of script. And each type differs in how it is supposed to be handled / invoked. Some scripts may
    be python modules, bash scripts, php scripts or whatever. Each of those can be supported by creating a subclass
    which implements the appropriate way to handle an invocation.

    Any kind of script wrapper is constructed by passing the script definition dict (the way it was initially described
    by users) as the only argument to the constructor. This dict has to contain at least the following fields to
    describe a valid script:

    - name: The string identifier by which the script can be invoked from within the ufotest system. Passing this name
      will be required for the script manager to select the appropriate script.
    - author: The string describing the name (and mail address) of the author which has created the script
    - path: The ABSOLUTE string path to the actual script file.
    - description: A string description of the purpose of the script and potentially other information one should have
      about it's behavior

    **EXPECTED IMPLEMENTATIONS**

    A subclass is expected to implement the "invoke" method. This method is supposed to handle actual execution of the
    script. Aside from that there are no hard requirements. The method accepts one argument, which could be anything
    depending on what is needed for that specific class. And the method should return the outcome of the script
    execution in some way. If it is a multitude of information preferably as a dict.
    """
    def __init__(self, script_definition: Dict[str, Any]):
        self.data = script_definition

    @abstractmethod
    def invoke(self, args: Optional[Any] = None) -> Any:
        raise NotImplementedError


class BashScript(AbstractScript):
    """
    This class represents a wrapper for storing the information about a bash script. It does not expect the passed
    script_definition to have any additional fields aside from those basic ones required for all AbstractScripts.
    """
    def __init__(self, script_definition: Dict[str, Any]):
        AbstractScript.__init__(self, script_definition)

        self.name = self.data['name']
        self.path = self.data['path']
        self.author = self.data['author']
        self.description = self.data['description']

    def invoke(self, args: Optional[str] = None) -> dict:
        folder = os.path.dirname(self.path)

        script_command = self.path
        if args is not None:
            script_command += f' {args}'

        completed_process = subprocess.run(
            script_command,
            cwd=folder,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return {
            'stdout':       completed_process.stdout.decode(),
            'stderr':       completed_process.stderr.decode(),
            'exit_code':    completed_process.returncode
        }


class MockScript(AbstractScript):
    """
    This is a mock implementation of AbstractScript mainly intended for testing purposes. It expects one additional
    field within the script_definition, aside from those required for all AbstractScript implementations:

    - code: This is a string field. The string should contain the python code which preferably evaluates to a single
      expression. When calling the invoke method of a mock script. This code will be dynamically interpreted with the
      "eval" builtin and the result of the expression will be returned as the result of the invoke method.
    """
    def __init__(self, script_definition: Dict[str, Any]):
        AbstractScript.__init__(self, script_definition)

        self.name = self.data['name']
        self.path = self.data['path']
        self.author = self.data['author']
        self.description = self.data['description']

        self.code = self.data['code']

    def invoke(self, args: Optional[str] = None) -> Any:
        return eval(self.code)


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
        self.fallback_script_definitions = self.config.pm.apply_filter(
            'fallback_script_definitions',
            self.fallback_script_definitions
        )
        self.fallback_scripts = {}

        self.build_script_definitions: List[dict] = self.config.get_ci_script_definitions()
        self.build_script_definitions = self.config.pm.apply_filter(
            'build_script_definitions',
            self.build_script_definitions
        )
        self.scripts = {}

    def load_fallback_scripts(self):
        for script_definition in self.fallback_script_definitions:
            self.register_fallback_script(script_definition)

    def register_fallback_script(self, script_definition: Dict[str, Any]) -> None:
        script_name = script_definition['name']
        script_class = eval(script_definition['class'])
        self.fallback_scripts[script_name] = script_class(script_definition)

    def register_script(self, script_definition: Dict[str, Any]) -> None:
        script_name = script_definition['name']
        script_class = eval(script_definition['class'])
        self.scripts[script_name] = script_class(script_definition)

    def load_scripts(self):
        pass

    def load_build_scripts(self, build_folder_path: str):
        # First of all within the build folder we need the path of the actual cloned repository folder. This repo
        # folder has the same name as the repo itself and this name should be given in the config
        repository_name = self.config.get_ci_repository_name()
        repository_path = os.path.join(build_folder_path, repository_name)

        # Now within the repository the scripts could be anywhere the user deems it appropriate. This is up to a
        # user preference. Because this might change, the relative locations (relative to the repo root folder) have
        # to be defined in the config for this to work.
        # The script definitions returned by this config method is a list of dicts just as with the fallback
        # scripts
        script_definitions = self.config.get_ci_script_definitions()
        for script_definition in script_definitions:
            # The major difference is that these still only contain relative paths for the script locations
            # so we'll need to change that to be the absolute paths within the folder we determined earlier
            script_path = os.path.join(repository_path, script_definition['relative_path'])
            script_definition['path'] = script_path

            self.register_script(script_definition)

    def most_recent_build_folder(self) -> str:
        """
        Returns the absolute path to the build folder of the most recent build.

        :returns: string of absolute path
        """


    def invoke(self, script_name: str, args: Optional[Any] = None, use_fallback: bool = False) -> Any:
        if use_fallback:
            script = self.fallback_scripts[script_name]
        else:
            script = self.scripts[script_name]

        return script.invoke(args)

    def __len__(self):
        return len(self.fallback_scripts)


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


