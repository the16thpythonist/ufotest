"""
Module containing all the actual console scripts of the project.
"""
import sys
import os
import json
from multiprocessing import Process
from pprint import pprint

import click
import matplotlib
import numpy as np
import shutil

from ufotest.config import PATH, get_config_path, Config
from ufotest.exceptions import IncompleteBuildError, BuildError, PciError, FrameDecodingError
from ufotest.util import (update_install,
                          run_command,
                          setup_environment,
                          init_install,
                          check_install,
                          execute_script,
                          get_version,
                          get_path,
                          check_vivado,
                          check_path)
from ufotest.util import cerror, cresult, ctitle, csubtitle, cprint, cparams
from ufotest.install import (mock_install_repository,
                             install_dependencies,
                             install_fastwriter,
                             install_pcitools,
                             install_libufodecode,
                             install_libuca,
                             install_uca_ufo,
                             install_ipecamera)
from ufotest.camera import save_frame, import_raw, set_up_camera, tear_down_camera, get_frame
from ufotest.testing import TestRunner, TestContext, TestReport
from ufotest.ci.build import BuildRunner, BuildReport, BuildLock, build_context_from_config
from ufotest.ci.server import server, BuildWorker


CONFIG = Config()

# == UTILITY FUNCTIONS ==


# == COMMANDS ==

# https://click.palletsprojects.com/en/8.0.x/complex/
# https://click.palletsprojects.com/en/8.0.x/complex/#interleaved-commands
pass_config = click.make_pass_decorator(Config)


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Print the version of the program')
@click.option('--verbose', '-v', is_flag=True, help='Print additional console output for the command')
@click.pass_context
def cli(ctx, version, verbose):
    """
    UfoTest command line interface

    The main way to use UfoTest's functionality is by invoking the appropriate command. Each command has it's own set
    of arguments and options. To list these options and to show an explanation of the commands purpose, use the
    --help option which is available for every command:

    ufotest <subcommand> --help
    """
    # If the version option of the base command is invoked, this means that we simply want to print the version of the
    # project and then terminate execution
    if version:
        # "get_version" reads the version of the software from the corresponding file in the source folder.
        version = get_version()
        click.secho(version, bold=True)
        sys.exit(0)

    # We acquire an instance of the config object here in the base command and then simply pass it as a context to each
    # respective sub command. Sure, the Config class is a singleton anyways and we could also invoke it in every
    # sub command, but like this we can do something cool. We simply add a --verbose option to this base command and
    # then save the value in the config, since we pass it along this also affects all sub commands and we dont need
    # to implement the --verbose option for every individual sub command.
    config = Config()
    config['context']['verbose'] = True
    ctx.obj = config

    # This fixes an important bug: Previously when any command was executed, the program attempted to call the prepare
    # method which would then in turn load the plugins. But that caused a problem when initially attempting to install
    # ufotest. For an initial installation there is not config file yet, but "prepare" and the init of the script and
    # plugin manager need certain config values! Thus ufotest could never be installed. Now we will treat the
    # installation command "init" as a special case which does not need the use the plugin system.
    if ctx.invoked_subcommand != 'init':
        config.prepare()


# -- Commands related to the installation of dependencies

#: A dictionary whose keys are possible string argument names for installable dependencies and the values are function
#: objects, which actually perform the installation of that dependency. Each of these functions should accept a single
#: positional argument which is the folder path into which they are supposed to be installed.
DEPENDENCY_INSTALL_FUNCTIONS = {
    'pcitool':              install_pcitools,
    'fastwriter':           install_fastwriter,
    'libufodecode':         install_libufodecode,
    'libuca':               install_libuca,
    'ipecamera':            install_ipecamera
}


# TODO: Add force flag
@click.command('install', short_help='Install a dependency for the ufo camera')
# https://click.palletsprojects.com/en/8.0.x/options/#choice-options
@click.argument('dependency', type=click.Choice(['pcitool', 'fastwriter', 'libufodecode', 'libuca', 'ipecamera']))
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
@click.option('--save-json', '-j', is_flag=True, help=(
    'Whether or not to create a JSON output file as a result of the installation process. The file will be located in '
    'the current working directory and be named "install.json" it will contain the keys: "success" (bool), '
    '"path": (string), "git": (string).'
))
@click.option('--skip', is_flag=True, help='Does not perform the actual installation. For testing.')
@pass_config
def install(config, dependency, path, save_json, skip):
    """
    Installs a given DEPENDENCY into the folder provided as PATH.

    This command is used to install individual dependencies for running the ufo camera system on the local machine.
    """
    # The path sting which is passed into this function could also be a relative path such as ".." which stands for
    # "the parent folder relative to the current one from which I am executing this". All functions expect an
    # absolute path and "realpath" converts these relative expressions into absolute paths
    path = os.path.realpath(path)

    # The "skip" flag is mainly for testing the CLI. It is supposed to prevent the actual functionality of
    # the command to be executed so the test case does not take so long. So in this case we do not actually
    # run the installation function, but still have to create a mock results dict
    if skip:
        result = mock_install_repository(path)
    else:
        # Each install function takes a single argument which is the folder path of the folder into which the
        # dependency (repo) is to be installed. They return a dict which describes the outcome of the installation
        # procedure with the following three fields: "success", "path", "git"
        install_function = DEPENDENCY_INSTALL_FUNCTIONS[dependency]
        result = install_function(path)

    # If the the "--save-json" flag was provided with the command, we'll also save the result of the installation
    # process as a JSON file to the current working directory.
    if save_json:
        try:

            json_path = os.path.join(os.getcwd(), 'install.json')
            with open(json_path, mode='w+') as file:
                json.dump(result, file, indent=4, sort_keys=True)

        except Exception as e:
            cerror(f'Could not save "install.json" because: {str(e)}')
            sys.exit(1)

    sys.exit(0)


@click.command('install-all', short_help='Install all project dependencies.')
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
@click.option('--no-dependencies', '-d', is_flag=True, help='Skip installation of required system packages')
@click.option('--save-json', '-j', is_flag=True, help=(
    'Whether or not to create a JSON output file as a result of the installation process. The file will be located in '
    'the current working directory and be named "install.json" it will contain the string names of the dependencies '
    'as keys and the values will be dicts, which in turn have the following keys: "success" (bool), '
    '"path": (string), "git": (string).'
))
@click.option('--skip', is_flag=True, help='Does not perform the actual installation. For testing.')
@pass_config
def install_all(config, path, no_dependencies, save_json, skip):
    """
    Installing all dependencies for the ufo camera project into PATH

    PATH has to be the path to an existing folder. The command installs all the required repositories into this folder.
    Apart from the repositories, the command also installs the required system packages for the operation of the
    UFO camera. For this it relies on the package installation method and operation system defined within the
    ufotest config file.
    """
    # The path sting which is passed into this function could also be a relative path such as ".." which stands for
    # "the parent folder relative to the current one from which I am executing this". All functions expect an
    # absolute path and "realpath" converts these relative expressions into absolute paths
    path = os.path.realpath(path)

    operating_system = CONFIG['install']['os']
    ctitle('INSTALLING NECESSARY REQUIREMENTS')
    cparams({
        'operating system': operating_system,
        'package install command': CONFIG['install'][operating_system]['package_install'],
        'camera dimensions:': f'{CONFIG.get_sensor_width()} x {CONFIG.get_sensor_height()}'
    })

    results = {}
    # We will only actually execute the installation procedures if the skip flag is not set
    if not skip:
        if no_dependencies:
            cprint('Skipping system packages...')
        else:
            install_dependencies(verbose=config.verbose())

        for dependency_name, install_function in DEPENDENCY_INSTALL_FUNCTIONS.items():
            csubtitle(f'Installing "{dependency_name}"')
            result = install_function(path)
            results[dependency_name] = result

    else:
        results['mock'] = mock_install_repository(path)

    # Creating the JSON file if the flag was set.
    if save_json:
        try:
            json_path = os.path.join(os.getcwd(), 'install.json')
            with open(json_path, mode='w+') as file:
                json.dump(results, file, indent=4, sort_keys=True)
        except Exception as e:
            cerror(f'Could not save "install.json" because: {str(e)}')
            sys.exit(1)

    sys.exit(0)


@click.command('init', short_help='Initializes the installation folder and config file for the app')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.option('--force', '-f', is_flag=True, help='Deletes the current installation to reinstall')
@click.option('--update', '-u', is_flag=True, help='Only update the static assets, leave data and configuration intact')
def init(verbose, force, update):
    """Initializes the installation folder for this application. This folder will be located at *$HOME/.ufotest*.
    This init includes the creation of the necessary folder structure for the archive and the tests, as well as the
    creation of the config file from a default template.
    """
    CONFIG['context']['verbose'] = verbose

    installation_path = get_path()
    ctitle('INITIALIZING UFOTEST INSTALLATION')
    cparams({'installation path': installation_path})

    if update:
        if check_path(installation_path, is_dir=True):
            update_install(installation_path)
            cresult('Updated ufotest installation')
            sys.exit(0)
        else:
            cerror('Cannot perform update without already existing installation!')
            sys.exit(1)

    if check_path(installation_path, is_dir=True):
        if force:
            shutil.rmtree(get_path())
            cprint('Deleted old installation folder')
        else:
            cerror('An installation folder already exists at the given path!')
            cerror('Please use the --force flag if you wish to forcefully replace the existing installation')
            sys.exit(1)
    else:
        cprint('    Installation folder does not yet exist')

    init_install(verbose=verbose)
    cresult('UfoTest successfully initialized, use the --help option for further commands')
    sys.exit(0)


@click.command('config', short_help='Edit the ufotest configuration file')
@click.option('--editor', '-e', type=click.STRING, help='Specify the editor command used to open the config file')
def config(editor):
    """
    Edit the ufotest configuration file
    """
    config_path = get_config_path()
    click.edit(filename=config_path, editor=editor)

    sys.exit(0)


@click.command('frame', short_help='Acquire and display a frame from the camera')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.option('--output', '-o', type=click.STRING,
              help='Specify the output file path for the frame', default='/tmp/frame.raw')
@click.option('--display', '-d', is_flag=True, help='display the frame in seperate window')
def frame(verbose, output, display):
    """
    Capture a single frame from the camera, save it as a file and optionally display it to the user
    """
    CONFIG['context']['verbose'] = verbose

    ctitle('CAPTURING FRAME')
    cparams({
        'output path': output,
        'display frame': display,
        'sensor_dimensions': f'{CONFIG.get_sensor_width()} x {CONFIG.get_sensor_height()}'
    })

    # Setup all the important environment variables and stuff
    setup_environment()
    exit_code, _ = run_command('rm /tmp/frame*')
    if not exit_code:
        cprint('Removed previous frame buffer')

    # ~ GET THE FRAME FROM THE CAMERA
    # "get_frame" handles the whole communication process with the camera, it requests the frame, saves the raw data,
    # decodes it into an image and then returns the string path of the final image file.
    try:
        frame_path = get_frame()
        shutil.copy(frame_path, output)
    except PciError as error:
        cerror('PCI communication with the camera failed!')
        cerror(f'PciError: {str(error)}')
        sys.exit(1)
    except FrameDecodingError as error:
        cerror('Decoding of the frame failed!')
        cerror(f'FrameDecodingError: {str(error)}')

    images = import_raw(
        path=output,
        n=1,
        sensor_height=CONFIG.get_sensor_height(),
        sensor_width=CONFIG.get_sensor_width()
    )

    if display:
        # An interesting thing is that matplotlib is imported in-time here and not at the top of the file. This actually
        # had to be changed due to a bug. When using ufotest in a headless environment such as a SSH terminal session
        # it would crash immediately, because a headless session does not work with the graphical matplotlib. Since
        # it really only is needed for this small section here, it makes more sense to just import it in-time.
        import matplotlib.pyplot as plt
        matplotlib.use('TkAgg')

        plt.imshow(images[0])
        plt.show()

    sys.exit(0)


@click.command('setup', short_help="Enable the camera")
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
def setup(verbose):
    if not check_install():
        return 1

    set_up_camera(verbose=verbose)


@click.command('teardown', short_help="Disable the camera. DO NOT USE")
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
def teardown(verbose):
    if not check_install():
        return 1

    tear_down_camera(verbose)


@click.command('flash', short_help='Flash a new .BIT file to the FPGA memory')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.argument('file', type=click.STRING)
def flash(verbose, file: str) -> None:
    """
    Flashes a given ".bit" FILE to the internal memory of the connected FPGA board

    FILE will be the string path of the file to be used for the flashing process.
    """
    CONFIG['context']['verbose'] = verbose

    # -- ECHO CONFIGURATION
    ctitle('FLASHING BITFILE TO FPGA')
    click.secho('--| bitfile path: {}\n'.format(file))

    # ~ CHECKING IF THE GIVEN FILE EVEN EXISTS
    file_path = os.path.abspath(file)
    file_exists = check_path(file_path, is_dir=False)
    if not file_exists:
        cerror('The given path for the bitfile does not exist')
        sys.exit(1)

    # ~ CHECKING IF THE FILE EVEN IS A BIT FILE
    file_extension = file_path.split('.')[-1].lower()
    is_bit_file = file_extension == 'bit'
    if not is_bit_file:
        cerror('The given path does not refer to file of the type ".bit"')
        sys.exit(1)

    # ~ CHECKING IF VIVADO IS INSTALLED
    vivado_installed = check_vivado()
    if not vivado_installed:
        cerror('Vivado is not installed, please install Vivado to be able to flash the fpga!')
        sys.exit(1)
    if CONFIG.verbose():
        cprint('Vivado installation found')

    # ~ STARTING VIVADO SETTINGS
    vivado_command = CONFIG['install']['vivado_settings']
    run_command(vivado_command, cwd=os.getcwd())
    if CONFIG.verbose():
        cprint('Vivado setup completed')

    # ~ FLASHING THE BIT FILE
    flash_command = "{command} -nolog -nojournal -mode batch -source fpga_conf_bitprog.tcl -tclargs {file}".format(
        command=CONFIG['install']['vivado_command'],
        file=file_path
    )
    exit_code = run_command(flash_command)
    if not exit_code:
        cresult('Flashed FPGA with: {}'.format(file_path))
        sys.exit(0)
    else:
        cerror('There was an error during the flashing of the FPGA')
        sys.exit(1)


@click.command('test', short_help="Run a camera test")
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.option('--suite', '-s', is_flag=True, help='Execute a test SUITE with the given name')
@click.argument('test_id', type=click.STRING)
def test(verbose, suite, test_id):
    """
    Run the test "TEST_ID"

    TEST_ID is a string, which identifies a certain test procedure. To view all these possible identifiers consult the
    config file.

    This command will execute either a single test case for the camera or a test suite, combines multiple test cases.
    The results of these tests will generate a test report. This test report will be saved into the archive of all
    test reports as a markdown and html file.
    """
    CONFIG['context']['verbose'] = verbose
    ctitle(f'RUNNING TEST{" SUITE" if suite else ""}')
    cparams({
        'test identifier': test_id,
        'is test suite': suite,
        'verbose': verbose
    })

    try:
        with TestContext() as test_context:
            # 1 -- DYNAMICALLY LOADING THE TESTS
            test_runner = TestRunner(test_context)
            test_runner.load()

            # 2 -- EXECUTING THE TEST CASES
            if suite:
                click.secho('    Executing test suite: {}...'.format(test_id), bold=True)
                test_runner.run_suite(test_id)
            else:
                click.secho('    Executing test: {}...'.format(test_id), bold=True)
                test_runner.run_test(test_id)

            # 3 -- SAVING THE RESULTS AS A REPORT
            test_report = TestReport(test_context)
            test_report.save(test_context.folder_path)

    except Exception as e:
        click.secho('[!] {}'.format(e), fg='red', bold=True)
        sys.exit(1)

    if verbose:
        click.secho(test_report.to_string())

    click.secho('(+) Test report saved to: {}'.format(test_context.folder_path), fg='green', bold=True)
    click.secho('    View the report at: http://localhost/archive/{}/report.html'.format(test_context.folder_name))

    sys.exit(0)


# == SCRIPTS COMMAND GROUP ==

@click.group('scripts', short_help='Command sub group for interacting with the scripts registered within ufotest')
@pass_config
def scripts(config):
    pass


@click.command('invoke', short_help='Invokes a script which is registered in ufotest identified by its string name')
@click.option('--args', type=click.STRING, default='',
              help=('This is a string which can contain additional arguments for the script itself. Depending on the '
                    'type of script, the concrete format of this may differ. For the default bash type, this string '
                    'is appended to the script call as it is.'))
@click.option('--fallback', is_flag=True, default=False,
              help=('Boolean flag of whether or not to use the fallback version of the script. The fallback version '
                    'is the (generally) stable version of a script which comes shipped with ufotest itself and is '
                    'not subject to version control.'))
@click.argument('name', type=click.STRING)
@pass_config
def invoke_script(config, name, args, fallback):
    """
    Invokes the script identified by it's string NAME.

    On default this command will attempt to invoke the most recent version of the script, which is subject to version
    control and came with the most recent CI build. To use the stable fallback version which comes with the
    ufotest software itself use the --fallback flag
    """
    ctitle('Invoking script')
    cparams({
        'script name': name,
        'additional args': args,
        'use fallback?': fallback,
    })

    try:
        result = config.sm.invoke(name, args, use_fallback=fallback)

        if result['exit_code'] == 0:
            cresult(f'script "{name}" exits with code 0')
            cprint('STDOUT:\n' + result['stdout'])

        elif result['exit_code'] != 0:
            cerror(f'script "{name}" exits with code 1')
            cerror('STDERR:\n' + result['stderr'])
            cprint('STDOUT:\n' + result['stdout'])
            sys.exit(1)

    except KeyError:
        cerror(f'A script with name "{name}" is not registered with ufotest!')
        sys.exit(1)

    sys.exit(0)


@click.command('list', short_help='Displays a list of all scripts which are registered with ufotest')
@click.option('--full', is_flag=True, default=False,
              help=('Boolean flag to show the full details of every script '))
@pass_config
def list_scripts(config, full):
    """
    Displays a list of all scripts that are registered with ufotest.

    Use the --detail flag to display more information about each script.
    """
    ctitle('list registered scripts')

    for script_name, script_wrapper in config.sm.scripts.items():
        csubtitle(f'{script_name} ({script_wrapper.data["class"]})')

        if full:
            details = {
                'description': script_wrapper.description,
                'author': script_wrapper.author,
                'path': script_wrapper.path,
                'has fallback?': script_name in config.sm.fallback_scripts,
            }
        else:
            details = {
                'path': script_wrapper.path,
                'has fallback?': script_name in config.sm.fallback_scripts
            }

        cparams(details)

    sys.exit(0)


@click.command('details', short_help='Displays the full details of a registered script including its source code')
@click.argument('name', type=click.STRING)
@pass_config
def script_details(config, name):
    """
    Shows the full details of the scripts identified by it's string NAME.

    This command prints the full details for the given script, including its source code.
    """
    # ~ Checking for eventual problems with the script
    # First we need to check if a script with the given name even exists
    if name in config.sm.scripts:
        script = config.sm.scripts[name]
    elif name in config.sm.fallback_scripts:
        script = config.sm.fallback_scripts[name]
    else:
        cerror(f'A script identified by "{name}" is nor registered with ufotest!')
        sys.exit(1)

    # Then we need to check if the file even exists / the content can be read, since we also want to display the
    # content of it
    try:
        with open(script.path, mode='r+') as file:
            content = file.read()
    except:
        cerror(f'The file {script.path} does not exists and/or is not readable!')
        sys.exit(1)

    # ~ Displaying the results to the user in case there are no problems

    ctitle(name)
    cparams({
        'type':         script.data['class'],
        'path':         script.path,
        'author':       script.author
    })

    cprint('DESCRIPTION:\n' + script.description)

    print()
    cprint('CONTENT:\n' + content)


# == CONTINUOUS INTEGRATION COMMAND GROUP ==
# The 'ci' sub command for ufotest is actually a command group which itself contains various sub commands related to
# the CI functionality such as starting the CI server or triggering a new build process with the remote repository.


@click.group('ci', short_help='continuous integration related commands')
def ci():
    pass


@click.command('build', short_help='Applies newest commit from remote repository and then executes test suite')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.option('--skip', '-s', is_flag=True, help='skip the cloning of the repository and flashing of the new bitfile')
@click.argument('suite', type=click.STRING)
def build(verbose, suite, skip) -> None:
    """
    Start a new CI build process using the test suite SUITE.

    A build process first clones the target repository, which was specified within the "ci" section of the config file.
    Specifically, it checks out the branch, which is also defined in the config, and uses the most recent commit to
    that branch. After the repository has been cloned, the bit file within is used to flash a new configuration onto
    the FPGA hardware. Finally, the given test suite is executed and the results are being saved to the archive.
    """
    CONFIG['context']['verbose'] = verbose

    # ~ PRINT CONFIGURATION
    ctitle('BUILDING FROM REMOTE REPOSITORY')
    cparams({
        'repository url': CONFIG.get_ci_repository_url(),
        'repository branch': CONFIG.get_ci_branch(),
        'bitfile relative path': CONFIG.get_ci_bitfile_path(),
        'test suite': suite
    })

    # ~ RUNNING THE BUILD PROCESS
    try:
        with build_context_from_config(CONFIG) as build_context:
            # The "build_context_from_config" function builds the context object entirely on the basis of the
            # configuration file, which means, that it also uses the default test suite defined there. Since the build
            # function is meant to be able to pass the test suite as a parameter, we will have to overwrite this piece
            # of config manually.
            build_context.test_suite = suite

            build_runner = BuildRunner(build_context)
            build_runner.run(test_only=skip)
            build_report = BuildReport(build_context)
            build_report.save(build_context.folder_path)
            sys.exit(0)

    except BuildError as e:
        cerror(f'An error has occurred during the build process...\n    {str(e)}')
        sys.exit(1)


@click.command('serve', short_help='Runs the CI server which serves the web interface and accepts build requests')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.option('--host', '-h', type=click.STRING, default='0.0.0.0', help='the host address for the server')
def serve(verbose, host):
    """
    Starts the CI web server. This web server serves the web interface for the application. Additionally it exposes an
    API, which automatically starts a new build process when a remote repository with the ufo source code registers a
    new push event.
    """
    # -- ECHO CONFIGURATION
    click.secho('\n| | STARTING CI SERVER | |', bold=True)
    click.secho('--| repository url: {}'.format(CONFIG.get_ci_repository_url()))
    click.secho('--| repository branch: {}'.format(CONFIG.get_ci_branch()))
    click.secho('--| bitfile path: {}'.format(CONFIG.get_ci_bitfile_path()))
    click.secho('--| host address: {}\n'.format(host))

    # So this might be confusing: Here we get the 'hostname', but the command also has an option called 'host'. The
    # 'host' option is an IP address. This IP address is the one, which the flask server will be bound to. It has to
    # be the IP address of the PC in the target *local* network, where it will receive the requests from a possibly
    # port-forwarded router. The 'hostname' is the domain name under which the server is addressed from the *outside*
    hostname = CONFIG.get_hostname()
    port = CONFIG.get_port()

    click.secho('(+) Visit the server at http://{}:{}/'.format(hostname, port), fg='green')

    # -- STARTING BUILD WORKER
    # The flask server does not actually process the actual builds. It simply accepts the requests and based on the
    # information within these requests it schedules a new build by putting the information into a queue. The actual
    # build will then be started by this separate build worker process. This is because builds can take a very long
    # time and they should not block the web server from handling other requests.
    build_worker = BuildWorker()
    process = Process(target=build_worker.run)
    process.start()

    # -- STARTING THE SERVER
    server.run(port=port, host=host)


# Registering the commands within the "ci" group. The ci group is a sub command group which contains the commands
# relating to the "continuous integration" functionality.
ci.add_command(build)
ci.add_command(serve)

# Registering the commands with the "scripts" group.
scripts.add_command(invoke_script)
scripts.add_command(list_scripts)
scripts.add_command(script_details)

# Registering the commands within the click group
cli.add_command(init)
cli.add_command(config)
cli.add_command(install)
cli.add_command(install_all)
cli.add_command(frame)
cli.add_command(setup)
cli.add_command(teardown)
cli.add_command(list_scripts)
cli.add_command(flash)
cli.add_command(test)

# Registering the sub groups
cli.add_command(ci)
cli.add_command(scripts)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
