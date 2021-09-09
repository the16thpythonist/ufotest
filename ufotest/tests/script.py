"""
This file is supposed to contain all ufotest TestCases which deal with the script system. More accurately: Those tests
which actually mainly test the script system itself, since technically every test interacts with the script system.
"""
import os

from ufotest.scripts import ScriptManager
from ufotest.testing import AbstractTest, TestRunner
from ufotest.testing import MessageTestResult, DictListTestResult


class LoadedScriptsTest(AbstractTest):

    name = 'loaded_scripts'
    description = (
        'Holy moly'
    )

    def __init__(self, test_runner: TestRunner):
        super(LoadedScriptsTest, self).__init__(test_runner)

        self.script_manager: ScriptManager = self.config.sm
        self.script_infos = {}

    def run(self):
        for script_name, script in self.script_manager.scripts.items():
            script_info = {
                '_name': script_name,
                '_title': '<span style="{}">{}</span>'.format(
                    'color: lightcoral;' if script.data['fallback'] else 'color: lightgreen;',
                    script_name
                ),
                'is_fallback': script.data['fallback'],
                'type': script.data['class']
            }
            self.script_infos[script_name] = script_info

        # The imperative of this test case could be formulated as "Every script should be part of the version control
        # system!". Thus we declare this test as failed if even any one of the scripts is not the build but the fallback
        # version.
        exit_code = any([info['is_fallback'] for info in self.script_infos.values()])

        return DictListTestResult(exit_code, self.script_infos)

