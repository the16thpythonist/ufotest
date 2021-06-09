import unittest
import warnings
from ufotest._testing import UfotestTestMixin

from ufotest.hooks import Filter, Action
from ufotest.scripts import ScriptManager, MockScript, AbstractScript


class TestScriptManager(UfotestTestMixin, unittest.TestCase):

    def setUp(self):
        # This method resets the plugin manager, meaning that it clears all registered callbacks from the action and
        # filter hooks. This is absolutely important so that we dont get interference from hooks registered in other
        # test methods.
        self.config.pm.reset()

    # -- simple tests --

    def test_construction_basically_works(self):
        """
        If a new object instance of ScriptManager can be created without errors
        """
        sm = ScriptManager(self.config)
        self.assertIsInstance(sm, ScriptManager)

    def test_registering_new_mock_fallback_script(self):
        """
        If a singular new fallback script can be manually registered by providing a script description dict
        """
        script_name = 'test'
        script_description = {
            'name':         script_name,
            'path':         '',
            'author':       'Jonas Teufel',
            'description':  'A mock ',
            'class':        'MockScript',
            'code':         ''
        }

        # We simply want to test if the registration process worked, thus we only check if the
        # length of the internal storage dict changes after adding the new script definition
        sm = ScriptManager(self.config)
        prev_length = len(sm.fallback_scripts)

        sm.register_fallback_script(script_description)
        length = len(sm.fallback_scripts)

        self.assertEqual(prev_length + 1, length)
        self.assertTrue(script_name in sm.fallback_scripts)
        self.assertIsInstance(sm.fallback_scripts[script_name], MockScript)

    def test_invoking_newly_registered_mock_script(self):
        """
        If a newly registered MockScript can be invoked from the script manager and on it's own
        """
        # MockScrips object's invoke methods will return whatever value the dynamically interpreted
        # code string "code" evaluates to. In this case we will make this be the code of a special string which
        # we can compare against later.
        script_name = 'test'
        script_return = 'The script returns this string!'
        script_description = {
            'name':         script_name,
            'path':         '',
            'author':       'Jonas Teufel',
            'description':  'A mock ',
            'class':        'MockScript',
            'code':         f'"{script_return}"'
        }

        sm = ScriptManager(self.config)
        sm.register_fallback_script(script_description)

        # Attempting to fetch the script object manually from the internal dict and then calling the invoke
        # method on it
        script = sm.fallback_scripts[script_name]
        self.assertIsInstance(script, MockScript)
        self.assertEqual(script_return, script.invoke())

        # Using the script managers wrapper method for invoking the scripts
        self.assertEqual(script_return, sm.invoke(script_name, use_fallback=True))

    def test_registering_script_basically_works(self):
        """
        If registering a normal script (not the fallback) version basically works
        """
        script_name = 'test'
        script_definition = {
            'name': script_name,
            'path': '',
            'author': 'Jonas Teufel',
            'description': 'A mock ',
            'class': 'MockScript',
            'code': ''
        }

        # We simply want to test if the registration process worked, thus we only check if the
        # length of the internal storage dict changes after adding the new script definition
        sm = ScriptManager(self.config)
        prev_length = len(sm.scripts)

        sm.register_fallback_script(script_definition)
        sm.register_script(script_definition)
        length = len(sm.scripts)

        self.assertEqual(prev_length + 1, length)
        self.assertTrue(script_name in sm.fallback_scripts)
        self.assertIsInstance(sm.scripts[script_name], MockScript)

    def test_registering_script_without_fallback_creates_warning(self):
        """
        If the attempt to register a script without a fallback version of the script (with the same identifier)
        existing properly triggers a UserWarning
        """
        script_name = 'test'
        script_definition = {
            'name': script_name,
            'path': '',
            'author': 'Jonas Teufel',
            'description': 'A mock ',
            'class': 'MockScript',
            'code': ''
        }

        sm = ScriptManager(self.config)

        with self.assertWarns(UserWarning):
            sm.register_script(script_definition)

    def test_invoking_non_existent_script_raises_key_error(self):
        """
        If invoking the "invoke" method with a non-existent script raises the proper key error
        """
        sm = ScriptManager(self.config)

        with self.assertRaises(KeyError):
            sm.invoke('unknown_script')

    def test_hello_world_script(self):
        """
        On default, one of the fallback scripts is supposed to be "hello_world.sh" which simply echos one string line
        "Hello World!". Here we check if this script is properly loaded and the bash invocation of it actually returns
        this string.
        """
        sm = ScriptManager(self.config)
        sm.load_fallback_scripts()

        self.assertIn('hello_world', sm.fallback_scripts)
        result = sm.invoke('hello_world', use_fallback=True)
        self.assertIsInstance(result, dict)
        self.assertIn('Hello World!', result['stdout'])

    # -- advanced tests --

    def test_fallback_script_definitions_hook(self):

        script_name = 'mock_script'

        @Filter('fallback_script_definitions', 10, config=self.config)
        def add_script_definition(script_definitions: list):
            return [{
                'name':         script_name,
                'path':         '',
                'author':       'Jonas Teufel',
                'description':  'A mock script',
                'class':        'MockScript',
                'code':         'None'
            }]

        sm = ScriptManager(self.config)
        sm.load_fallback_scripts()
        # Now since we completely overwrote the value in the filter hook, the list of
        # fallback scripts should now contain only this item.
        self.assertEqual(1, len(sm.fallback_scripts))
        self.assertTrue(script_name in sm.fallback_scripts)

    def test_script_manager_pre_construct_hook(self):

        custom_value = 3.141

        @Action('script_manager_pre_construct', 10, config=self.config)
        def add_custom_attribute(sm, namespace):
            setattr(sm, 'custom_attribute', custom_value)

        sm = ScriptManager(self.config)
        sm.load_fallback_scripts()

        self.assertTrue(hasattr(sm, 'custom_attribute'))
        self.assertEqual(custom_value, sm.custom_attribute)

    def test_creating_custom_script_wrapper_implementation_works(self):

        # First we actually need to create a custom implementation of the AbstractScript base class.
        # For testing: This type of script will always return int 42 on invocation
        class CustomScript(AbstractScript):

            def __init__(self, script_definition):
                AbstractScript.__init__(self, script_definition)

            def invoke(self, args=None):
                return 42

        # Now we need to attach this class as a custom property to the script manager
        # using the pre construct hook
        @Action('script_manager_pre_construct', 10, config=self.config)
        def register_custom_script_class(this, namespace):
            namespace['CustomScript'] = CustomScript

        # Then we also need to use the script definitions filter hook to insert a script of this
        # type to be loaded.
        @Filter('fallback_script_definitions', 10, config=self.config)
        def add_custom_script(script_definitions):
            return [{
                'name':         'custom_script',
                'author':       'Jonas Teufel',
                'description':  'a custom script',
                'path':         '',
                'class':        'CustomScript'
            }]

        # Now during the construction of the script manager, these hooks should be invoked
        sm = ScriptManager(self.config)
        sm.load_fallback_scripts()

        self.assertTrue('custom_script' in sm.fallback_scripts)
        self.assertIsInstance(sm.fallback_scripts['custom_script'], CustomScript)
