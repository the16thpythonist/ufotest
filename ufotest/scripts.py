import os
import json
import copy
import datetime
import warnings
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from abc import abstractmethod


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

    def invoke(self, args: Optional[dict] = None) -> dict:
        folder = os.path.dirname(self.path)

        script_command = self.path
        if isinstance(args, dict):
            script_command = f'{args["prefix"]} {script_command} {args["postfix"]}'

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
        self.config.pm.do_action('script_manager_pre_construct', self, globals())

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
        """
        Based on the given *script_definition", registers the script in question in the internal "fallback_scripts"
        dict. To do that the script will be converted into the appropriate script wrapper instance.

        :param script_definition: The dict which describes the script to be registered. It's required fields depend
            on what type (class field) the script is of.

        :returns: void
        """
        script_name = script_definition['name']
        script_class = eval(script_definition['class'])
        self.fallback_scripts[script_name] = script_class(script_definition)

    def register_script(self, script_definition: Dict[str, Any]) -> None:
        """
        Based on the given *script_definition", registers the script in question in the internal "scripts" dict. To
        do that the script will be converted into the appropriate script wrapper instance.

        Note that this method will create a warning when attempting to register a script with an identifier for which
        no fallback script exists.

        :param script_definition: The dict which describes the script to be registered. It's required fields depend
            on what type (class field) the script is of.

        :returns: void
        """
        # We will allow a script to be registered without a fallback scripts, because there might be a method to the
        # madness so to say, but we will at least warn, that this is not how it is intended.
        if script_definition['name'] not in self.fallback_scripts:
            warnings.warn((
                f'It seems like you are registering a script identified by "{script_definition["name"]}". For this '
                f'identifier no fallback script exists. Be aware, that should the script not work or be absent in the '
                f'future functionality might break without a stable fallback version to replace it with!'
            ), UserWarning)

        script_name = script_definition['name']
        script_class = eval(script_definition['class'])
        self.scripts[script_name] = script_class(script_definition)

    def load_scripts(self) -> None:
        """
        This method loads all dem scripts.

        After this method was called it can be assumed that a reference to all registered scripts has been loaded to
        the internal values "self.fallback_scripts" and "self.scripts" respectively.

        This method first loads the fallback scripts. These are part of the main ufotest code. The scripts which are
        loaded are defined by the internal "fallback_script_definitions" list. The actual internal dict for the
        scripts (self.scripts) is then initialized as a copy of these fallback scripts. Then it is attempted to load
        the script from the latest cloned version of the remote repository (ci repo) and overwrite the self.script
        entries with those.

        :returns: None
        """
        # First of we load the fallback scripts. These are the scripts which are the hardcoded stable versions which
        # come shipped with the actual ufotest code.
        self.load_fallback_scripts()
        # Then we will use these fallback scripts as the "default" versions of the main script dict. In the next step
        # when loading the scripts from the remote repo, they will most likely be overwritten, but if a script is
        # missing in the repo, that wont break our code (the whole purpose of a fallback)
        self.scripts = copy.deepcopy(self.fallback_scripts)

        try:
            # This method returns the absolute path to the build folder of the most recent build. That is the build
            # from which we want to use the scripts. If NONE builds exist yet, this raises a LookupError!
            build_folder_path = self.most_recent_build_folder()
            # Given the folder path of a build folder, this method uses the ci script definitions to load all the
            # appropriate script wrapper instances into the self.scripts dict from this build.
            self.load_build_scripts(build_folder_path)
        except LookupError:
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

    # TODO: We are actually calculating this every time here. This is not the most efficient solution.
    # If this becomes an issue in the future we can for example cache the current most recent result in a file
    # whenever a test report is created...
    def most_recent_build_folder(self) -> str:
        """
        Returns the absolute path to the build folder of the most recent build.

        :raises LookupError: In case there are no builds yet, on other words: If the remote repo has never been
            cloned before, no scripts can be loaded from it either.
        :returns: string of absolute path
        """
        # Well the dumb solution would be to parse the name of each build folder because part of the name is when
        # the build was started. But the concrete format or the containing of the date itself could be subject to
        # future change. I think each build folder also should contain a json file which contains the details of the
        # build.
        builds = []
        builds_path = self.config.get_builds_path()

        for root, folders, files in os.walk(builds_path):
            if len(folders) == 0:
                raise LookupError((
                    'The builds folder of this ufotest installation is empty. This means that the remote repo has not '
                    'been cloned at this point. Thus, no scripts can be loaded from the remote repository.'
                ))

            for folder in folders:
                folder_path = os.path.join(root, folder)
                folder_stat = os.stat(folder_path)
                builds.append({
                    'path': folder_path,
                    'creation_time': folder_stat.st_ctime
                })
            break

        most_recent_build = max(builds, key=lambda b: datetime.datetime.fromisoformat(b['creation_time']))
        return most_recent_build['path']

    def invoke(self, script_name: str, args: Optional[Any] = None, use_fallback: bool = False) -> Any:
        """
        This method invokes the script identified by *script_name* passing the optional *args*. If the *use_fallback*
        flag is set it will attempt to use the fallback version.
        """
        if use_fallback:
            # We dont actually need to check this here, because if this entry actually did not exist in the dict, this
            # would raise a key error anyways. But that key error would be very unspecific and hard to debug, so it's
            # better to raise the error on our terms.
            if script_name not in self.fallback_scripts:
                raise KeyError((f'You are attempting to invoke a fallback script identified by "{script_name}", '
                                f'but no script with this identifier has been registered as a fallback script. '
                                f'Check if the given identifier has a typo and if the script was properly registered!'))

            script = self.fallback_scripts[script_name]
        else:
            if script_name not in self.scripts:
                raise KeyError((f'You are attempting to invoke a script identified by "{script_name}", '
                                f'but no script with this identifier was previously registered as a script. '
                                f'Check if the given identifier has a type and if the script was properly registered!'))

            script = self.scripts[script_name]

        # Returning the result of the actual script invocation.
        return script.invoke(args)

    def get(self, script_name: str, use_fallback: bool = False) -> AbstractScript:
        if use_fallback:
            if script_name not in self.fallback_scripts:
                raise KeyError((f'You are attempting to retrieve a fallback script identified by "{script_name}", '
                                f'but no script with this identifier has been registered as a fallback script!'))

            return self.fallback_scripts[script_name]

        else:
            if script_name not in self.scripts:
                raise KeyError((f'You are attempting to retrieve a fallback script identified by "{script_name}", '
                                f'but no script with this identifier has been registered as a fallback script!'))

            return self.scripts[script_name]

    def __len__(self):
        return len(self.fallback_scripts)



