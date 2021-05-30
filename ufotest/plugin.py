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
# TODO: Add ignorelist


class PluginManager:

    def __init__(self, plugin_folder_path: str = ''):
        self.plugin_folder_path = plugin_folder_path

        self.plugins = {}

        self.filters = defaultdict(list)
        self.actions = defaultdict(list)

    # -- For invoking hooks in the main system --

    def do_action(self, hook_name: str, *args, **kwargs) -> None:
        if hook_name in self.actions.keys():
            callback_specs = sorted(self.actions[hook_name], key=lambda spec: spec['priority'], reverse=True)
            callbacks = [spec['callback'] for spec in callback_specs]
            for callback in callbacks:
                callback(*args, **kwargs)

    def apply_filter(self, hook_name: str, value: Any, *args, **kwargs) -> Any:
        filtered_value = value

        if hook_name in self.filters.keys():
            callback_specs = sorted(self.filters[hook_name], key=lambda spec: spec['priority'], reverse=True)
            callbacks = [spec['callback'] for spec in callback_specs]
            for callback in callbacks:
                filtered_value = callback(filtered_value, *args, **kwargs)

        return filtered_value

    # -- For registering hook callbacks in the plugins --

    def register_filter(self, hook_name: str, callback: Callable, priority: int = 10) -> None:
        self.filters[hook_name].append({
            'callback':         callback,
            'priority':         priority
        })

    def register_action(self, hook_name: str, callback: Callable, priority: int = 10) -> None:
        self.actions[hook_name].append({
            'callback':         callback,
            'priority':         priority
        })

    # -- Loading the plugins --

    def load_plugins(self):

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

    @classmethod
    def import_plugin_by_path(cls, path: str) -> Tuple[str, Any]:
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


