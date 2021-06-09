import os
import sys
import importlib.util

from typing import Any, Callable, Tuple
from collections import defaultdict

"""
PLANNING

So I want the plugin manager to work really similar to how the hook system in Wordpress works:
https://developer.wordpress.org/plugins/hooks/
Thats because I already have a lot of experience with that system and I kind of really like it. It just makes sense
and is rather intuitive to use. The main point is that it uses hooks: A hook is essentially a point in the execution
of the main program where a plugin can insert custom functionality to be executed. Wordpress differs between two
types of hooks: action hooks simply allow the execution of code, they dont have a return value. filter hooks allow
the modification of certain important values of the main program.
"""


class PluginManager:
    """
    This class represents the plugin manager which is responsible for managing the plugin related functionality for
    ufotest. This mainly included the dynamic discovery and loading of the plugins at the beginning of the program
    execution and the management and application of the additional action and filter hooks added by those plugins.

    **UFOTEST PLUGIN SYSTEM**

    The ufotest plugin system is strongly influenced by the Wordpress plugin system
    (https://developer.wordpress.org/plugins/hooks/). It uses so called hooks to enable plugins to insert custom
    functions to be executed at vital points during the ufotest main program routine. A plugin simply has to decorate
    a function with the according hook decorator and supply a string identifier for which hook to use. The function
    will then be registered within the plugin manager and wait there until the according hook is actually called from
    within the main routine.
    The plugin system differentiates between two types of hooks: *action* hooks dont have a return value, if a function
    is hooked into an action hook, this just means that it will be executed at a certain point. *filter* hooks on the
    other side have a return value. Filter hooks present the possibility to modify certain key data structures during
    the execution of the main ufotest routine.

    **USING THE PLUGIN MANAGER**

    Alongside the config instance for ufotest, the plugin manager instance is the second most important thing. It has
    to be accessible by all parts of the code at any time. This is because the individual parts of the code actually
    invoke the special hooks by referencing the plugin manager. To create a new instance of the pm it only needs the
    folder which is supposed to contain the plugins. After creating the instance, the "load_plugins" method has to be
    used to actually load the plugins from that folder. At this point the internal dicts "filters" and "actions"
    already contain all the callable instance linked to the specific hooks, just waiting to be executed. Invoking a
    hook within the main routine can be done with the "do_action" and "apply_filter" methods.

    .. code-block:: python

        pm = PluginManager("/path/to/plugins")
        pm.load_plugins()

        # Some time later
        data = {}
        data_filtered = pm.apply_filter("custom_filter", data)

        pm.do_action("custom_action")

    **LOADING THE PLUGINS**

    The plugins themselves are dynmically imported during the runtime of the ufotest routine. The plugin manager will
    attempt to import the plugins from the folder which was passed to its constructor. Some important assumptions are
    made about what constitutes a valid plugin:

    - Each plugin is assumed to be a FOLDER. The folder name will be used as the plugin name, by which it will be
      identified
    - Within each plugin folder there has to be at least a "main.py" python module. This is what is actually imported
      by the plugin system. Consequentially, all of it's top level code will be executed on import time.
    - Important detail: Folders starting with an underscore will be ignored! This is mainly a pragmatic choice to make
      sure that the plugin system does not attempt to import __pycache__ but can also be used to quickly disable
      plugins
    """
    def __init__(self, plugin_folder_path: str = ''):
        self.plugin_folder_path = plugin_folder_path

        self.plugins = {}

        self.filters = defaultdict(list)
        self.actions = defaultdict(list)

    # -- For invoking hooks in the main system --

    def do_action(self, hook_name: str, *args, **kwargs) -> None:
        """
        Executes all the plugin functions which have been hooked to the action hook identified by *hook_name*.

        The hook call may include additional positional and keyword arguments which are passed as they are to the
        registered callbacks.

        :param hook_name: The string name identifying the hook to be executed.
        :return: void
        """
        if hook_name in self.actions.keys():
            callback_specs = sorted(self.actions[hook_name], key=lambda spec: spec['priority'], reverse=True)
            callbacks = [spec['callback'] for spec in callback_specs]
            for callback in callbacks:
                callback(*args, **kwargs)

    def apply_filter(self, hook_name: str, value: Any, *args, **kwargs) -> Any:
        """
        Applies all the plugin callback functions which have been hooked to the filter hook identified by *hook_name*
        to filter the given *value*. The result of each filter operation is then passed as the value argument to the
        next filter callback in order of priority.

        The hook call may include additional positional and keyword arguments which are passed as they are to the
        registered callbacks.

        :param hook_name: THe string name identifying the hook to be executed.
        :param value: Whatever value that specific hook is supposed to manipulate

        :return: The manipulated version of the passed value argument
        """
        filtered_value = value

        if hook_name in self.filters.keys():
            callback_specs = sorted(self.filters[hook_name], key=lambda spec: spec['priority'], reverse=True)
            callbacks = [spec['callback'] for spec in callback_specs]
            for callback in callbacks:
                filtered_value = callback(filtered_value, *args, **kwargs)

        return filtered_value

    # -- For registering hook callbacks in the plugins --

    def register_filter(self, hook_name: str, callback: Callable, priority: int = 10) -> None:
        """
        Registers a new filter *callback* function for the hook identified by *hook_name* with the given *priority*.

        :param hook_name: The name of the hook for which to register the function
        :param callback: A callable object, which is then actually supposed to be executed when the according hook is
            invoked. Since this is a filter hook, the callback needs to accept at least one argument which is the
            value to be filtered and it also needs to return a manipulated version of this value.
        :param priority: The integer defining the priority of this particular callback. Default is 10.
        :return: void
        """
        self.filters[hook_name].append({
            'callback':         callback,
            'priority':         priority
        })

    def register_action(self, hook_name: str, callback: Callable, priority: int = 10) -> None:
        """
        Registers a new action *callback* function for the hook identified by *hook_name* with the given *priority*.

        :param hook_name: The name of the hook for which to register the function
        :param callback: A callable object, which is then actually supposed to be executed when the according hook is
            invoked.
        :param priority: The integer defining the priority of this particular callback. Default is 10.
        :return: void
        """
        self.actions[hook_name].append({
            'callback':         callback,
            'priority':         priority
        })

    # -- Loading the plugins --

    def load_plugins(self):
        """
        Loads all the plugins from the plugin folder which was passed to the constructor of the manager instance.

        After this method was executed, it can be assumed that the internal dicts "filters" and "actions" contain all
        the callable instance linked to the according hook names.

        :return: void
        """
        for root, folders, files in os.walk(self.plugin_folder_path, topdown=True):

            for folder_name in folders:
                # IMPORTANT: We will ignore all folders which start with and underscore. The very practical reason for
                # this is that the plugins folder will almost certainly contain a __pycache__ folder which obviously
                # is not a ufotest plugin and thus cause an error. But this behaviour is also nice to disable certain
                # plugins without removing them completely: simply rename them to start with an underscore
                if folder_name[0] == '_':
                    continue

                plugin_path = os.path.join(root, folder_name)
                plugin_name, module = self.import_plugin_by_path(plugin_path)
                self.plugins[plugin_name] = module

    def reset(self):
        """
        Resets the plugin manager, which means that it unloads all registered filter and action hooks. Also clears the
        internal reference to all the plugin modules.

        :returns: void
        """
        self.filters = defaultdict(list)
        self.actions = defaultdict(list)

        self.plugins = {}

    @classmethod
    def import_plugin_by_path(cls, path: str) -> Tuple[str, Any]:
        """
        Given the path of a folder, this method will attempt to dynamically import a "main.py" module within this
        folder interpreting it as a ufotest plugin.

        :return: A tuple of two elements, where the first is the string name of the plugin and the second is the
            imported module instance.
        """
        plugin_name = os.path.basename(path)
        plugin_main_module_path = os.path.join(path, 'main.py')
        if not os.path.exists(plugin_main_module_path):
            raise FileNotFoundError((
                f'Cannot import folder "{plugin_name}" as an ufotest plugin, because the folder does not contain a '
                f'main.py python module. All ufotest plugins need to have a main.py file! This is the top level file '
                f'which is imported to import the plugins functionality into the ufotest system.'
            ))

        spec = importlib.util.spec_from_file_location(plugin_name, plugin_main_module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[plugin_name] = module

        return plugin_name, module


