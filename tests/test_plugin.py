import os
import tempfile
import unittest

from ufotest._testing import UfotestTestMixin
from ufotest.plugin import PluginManager
from ufotest.hooks import Action, Filter


class TestPluginManager(unittest.TestCase):

    def test_construction_works(self):
        pm = PluginManager()
        self.assertIsInstance(pm, PluginManager)
        # At the beginning the hook registries for action and filter hooks should be empty
        self.assertEquals(0, len(pm.actions))
        self.assertEquals(0, len(pm.filters))

    def test_registering_filter_works(self):
        pm = PluginManager()

        # First we need to register a function to be applied for the filter
        def square(value: int):
            return value ** 2

        pm.register_filter('custom_value', square)

        # Then we need to invoke this exact hook
        value = 3
        filtered_value = pm.apply_filter('custom_value', value)

        self.assertEqual(filtered_value, value ** 2)

    def test_registering_same_filter_twice_works(self):
        pm = PluginManager()

        def square(value: int):
            return value ** 2

        pm.register_filter('custom_value', square)
        pm.register_filter('custom_value', square)

        value = 3
        filtered_value = pm.apply_filter('custom_value', value)

        # Squaring a number twice should come out as the same as taking it to the 4th power
        self.assertEqual(filtered_value, value ** 4)

    def test_filter_priority_works(self):
        pm = PluginManager()

        def append_one(value: list):
            value.append(1)
            return value

        def append_two(value: list):
            value.append(2)
            return value

        # Now we will register the two filter functions in such a way that if the priorities work it should come out
        # as [1, 2], but if it is strictly only using the order of registering it would be [2, 1]
        pm.register_filter('modify_list', append_two, priority=10)
        pm.register_filter('modify_list', append_one, priority=100)

        value = []
        filtered_value = pm.apply_filter('modify_list', value)
        self.assertEquals([1, 2], filtered_value)

    def test_import_plugin_by_path_works(self):

        with tempfile.TemporaryDirectory() as folder_path:
            # First we need to create a mock plugin: This will be a folder which contains a single python module with
            # the name "main.py" This module needs to contain at least some code with which we can verify that it is
            # actually being loaded
            plugin_name = 'my_plugin'
            plugin_folder_path = os.path.join(folder_path, plugin_name)
            os.mkdir(plugin_folder_path)

            plugin_module_name = 'main.py'
            plugin_module_path = os.path.join(plugin_folder_path, plugin_module_name)
            plugin_module_content = 'CONSTANT = 125'
            with open(plugin_module_path, mode='w+') as file:
                file.write(plugin_module_content)

            # Now we attempt to import it
            name, module = PluginManager.import_plugin_by_path(plugin_folder_path)
            self.assertEquals(plugin_name, name)
            self.assertEquals(125, module.CONSTANT)


class TestHookDecorators(UfotestTestMixin, unittest.TestCase):

    def test_action_decorator(self):

        @Action('my_action', 10, config=self.config)
        def change_value(value: list):
            value.append(1)

        value = []  # The action hook will have to add a value to this for the assert to be successful
        self.config.pm.do_action('my_action', value)

        self.assertNotEqual(0, len(value))

    def test_filter_decorator(self):

        @Filter('modify_value', 10, config=self.config)
        def square(value: int):
            return value ** 2

        value = 3
        filtered_value = self.config.pm.apply_filter('modify_value', value)
        self.assertEquals(value ** 2, filtered_value)


class TestMockPlugin(UfotestTestMixin, unittest.TestCase):

    MOCK_PLUGIN_CONTENT = '\n'.join([
        'from ufotest.hooks import Action, Filter',
        '',
        '@Filter("modify_value", 10)',
        'def square(value: int):',
        '    return value ** 2',
        '',
        '@Action("raise_errors", 10)',
        'def key_error():',
        '    raise KeyError("moin")',
        '',
    ])

    @classmethod
    def setUpClass(cls):
        # Obviously we need to execute the code of "UfotestTestMixin" first, which will provide us with the necessary
        # temporary folder and ufotest installation
        super(TestMockPlugin, cls).setUpClass()

        # Now we actually create the plugin
        plugin_folder_path = os.path.join(cls.folder_path, 'plugins')
        if not os.path.exists(plugin_folder_path):
            os.mkdir(plugin_folder_path)

        cls.plugin_name = 'my_plugin'
        cls.plugin_path = os.path.join(plugin_folder_path, cls.plugin_name)
        os.mkdir(cls.plugin_path)

        plugin_module_name = 'main.py'
        plugin_module_path = os.path.join(cls.plugin_path, plugin_module_name)
        with open(plugin_module_path, mode='w+') as file:
            file.write(cls.MOCK_PLUGIN_CONTENT)

        # We need to update the plugin manager in the config file, since our plugin did not exist during the initial
        # loading
        cls.config.pm = PluginManager(plugin_folder_path=plugin_folder_path)
        cls.config.pm.load_plugins()

    def test_plugin_is_loaded(self):
        self.assertNotEqual(0, len(self.config.pm.plugins))
        self.assertIn(self.plugin_name, self.config.pm.plugins)

    def test_plugin_hooks_actually_register(self):

        with self.assertRaises(KeyError):
            self.config.pm.do_action('raise_errors')

        value = 3
        filtered_value = self.config.pm.apply_filter('modify_value', value)
        self.assertEquals(value ** 2, filtered_value)
