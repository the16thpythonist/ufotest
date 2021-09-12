"""
This file is supposed to contain all ufotest TestCases which deal with the script system. More accurately: Those tests
which actually mainly test the script system itself, since technically every test interacts with the script system.
"""
import os
import difflib

from ufotest.scripts import ScriptManager
from ufotest.testing import AbstractTest, TestRunner
from ufotest.testing import MessageTestResult, DictListTestResult
from ufotest.util import cprint
from ufotest.util import run_command


class ScriptTest(AbstractTest):

    BOOLEAN_COLORS = {
        True: 'lightgreen',
        False: 'lightcoral'
    }

    def __init__(self, test_runner: TestRunner):
        super(ScriptTest, self).__init__(test_runner)

        self.script_manager = self.config.sm
        self.script_infos = {}

    def format_boolean_span(self, content: str, status: bool) -> str:
        """
        Creates a HTML span element using the given *content* and styling it with color according to the additional
        boolean *status* value.

        :param str content: The actual string content which is supposed to be placed within the span tags
        :param bool status: The boolean status value which determines the styling of the span element

        :returns: The html string
        """
        return '<span style="color: {};">{}</span>'.format(
            self.BOOLEAN_COLORS[status],
            content
        )


class LoadedScriptsTest(AbstractTest):

    name = 'loaded_scripts'
    description = (
        'This test will check if all build version of the external scripts have been loaded. The external scripts are '
        'usually bash scripts which manage the actual interfacing with the camera hardware. By default, ufotest ships '
        '(relatively) stable fallback versions of those with the source code itself, so that ufotest can be used '
        'out of the box, but when using the CI system, these scripts should be part of the version control repository. '
        'This is what this test will check. It will attempt to load all vital scripts, display some info and check if '
        'a dynamic version of a recent build is loaded or if a fallback version is loaded. The test will "fail" if '
        'even one of the scripts is NOT loaded from a build.'
    )

    def __init__(self, test_runner: TestRunner):
        super(LoadedScriptsTest, self).__init__(test_runner)

        self.script_manager: ScriptManager = self.config.sm
        self.script_infos = {}

    def run(self):
        for script_name, script in self.script_manager.scripts.items():

            file_name = os.path.basename(script.data['path'])

            script_info = {
                '_name': script_name,
                '_title': '<span style="{}">{}</span>'.format(
                    'color: lightcoral;' if script.data['fallback'] else 'color: lightgreen;',
                    script_name
                ),
                'is_fallback': script.data['fallback'],
                'type': script.data['class'],
                'file': file_name,
                'is_readable': os.path.isfile(script.data['path']),
            }

            # If the file is indeed readable then we are going ro read it to get more information about it.
            if script_info['is_readable']:

                # First additional nice-to-have bit of information is the length of the file. This will help with
                # spotting if somehow an empty file has been loaded and that is causing issues
                with open(script.data['path'], mode='r') as file:
                    script_lines = file.readlines()

                script_info['length'] = f'{len(script_lines)} lines'

                # Another interesting one is to also load the fallback file and compute how many lines are
                # different between the fallback version and the build version. This can also help spotting problems
                # with perhaps not having committed any changes.
                fallback_script = self.script_manager.fallback_scripts[script_name]
                with open(fallback_script.data['path'], mode='r') as file:
                    fallback_script_lines = file.readlines()

                fallback_diff = len([line for line in script_lines if line not in fallback_script_lines])
                script_info['diff'] = f'{fallback_diff} lines'

            # If the script is not a fallback we can do another nifty thing for the report: We can provide the url to
            # download this file from the web server.
            if not script_info['is_fallback'] and 'relative_path' in script.data:
                # TODO: This is not a good thing. I am hacking the url together from implicit assumptions but I should
                #       really be having a dedicated variable or method to wrap this
                repository_path = script.data['path'].rstrip(script.data['relative_path'])
                repository_name = os.path.basename(repository_path)

                build_path = os.path.dirname(repository_path)
                build_name = os.path.basename(build_path)

                relative_url = os.path.join('builds', build_name, repository_name, script.data['relative_path'])
                absolute_url = self.config.url(relative_url)

                # The "file" field already exists and provides the filename for that script. In this case we are going
                # to replace this simple string with a hyperlink
                script_info['file'] = '<a class="link" style="opacity: 0.6;" href="{}">{}</a>'.format(
                    absolute_url,
                    file_name
                )
                # A hidden field to indicate the
                script_info['_file_url'] = absolute_url

            self.script_infos[script_name] = script_info
            cprint(f'processed script {script_name}')

        # The imperative of this test case could be formulated as "Every script should be part of the version control
        # system!". Thus we declare this test as failed if even any one of the scripts is not the build but the fallback
        # version.
        exit_code = any([info['is_fallback'] for info in self.script_infos.values()])

        return DictListTestResult(exit_code, self.script_infos)


class ScriptSyntaxTest(ScriptTest):

    name = 'scripts_syntax'

    description = (
        'This test checks if any of the loaded scripts has a syntax error. The test will fail if even one of the '
        'loaded scripts has a syntax error. A script is also declared to have an error if the script file could not '
        'be found at all. Only if a script has an error, the error message will appear in the listing below.'
    )

    def __init__(self, test_runner: TestRunner):
        super(ScriptSyntaxTest, self).__init__(test_runner)

        self.script_manager: ScriptManager = self.config.sm

    def run(self):

        for script_name, script in self.script_manager.scripts.items():

            # For each script in the list of all scripts loaded by the script manager we are going to assemble a
            # script_info dict, which will be the basis for a DictListTestResult. On default we assume that the script
            # has no errors, then test all the possible ways an error could occur and override the default False in
            # those cases.
            script_info = {
                '_name': script_name,
                'has_error': False,
                'method': script.syntax_check_method,
                'error': 'none'
            }

            # ~ FILE ACCESSIBLE
            # A first source for an error could be that the file cannot be accessed at all. This is obviously much
            # worse than a syntax error, because it means there is something fundamentally wrong with the
            script_path = script.data['path']
            if not script_info['has_error'] and not os.path.exists(script_path):
                script_info['has_error'] = True
                script_info['error'] = f'No script exists at the path "{script_path}"'

            # ~ SYNTAX ERROR
            # Conveniently the bash system itself offers a very easy way of checking script syntax, the script file
            # simply has to be invoked with "bash -n".
            syntax_ok, error_message = script.check_syntax()
            if not script_info['has_error'] and not syntax_ok:
                script_info['has_error'] = True
                script_info['error'] = f'{error_message}'

            # At the end we can determine the status of the script by whether or not the has_error flag has been set
            # during the previous checks. We have to negate the flag because format_boolean_span will format True as
            # green (=good) and False as red (=bad)
            script_info['_title'] = self.format_boolean_span(script_name, not script_info['has_error'])
            self.script_infos[script_name] = script_info

            cprint(f'Checked syntax of {script_name}')

        # The test will be considered as failed if even a single script has a syntax error!
        exit_code = int(any([script_info['has_error'] for script_info in self.script_infos.values()]))
        return DictListTestResult(exit_code, self.script_infos)
