import unittest
from ufotest._testing import UfotestTestMixin

from ufotest.scripts import ScriptManager, MockScript


class TestScriptManager(UfotestTestMixin, unittest.TestCase):

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
