"""
Module containing all the actual console scripts of the project.
"""
import sys
import os
from multiprocessing import Process

import click
import matplotlib
import numpy as np
import shutil

from ufotest.config import PATH, get_config_path, Config
from ufotest.scripts import SCRIPTS, SCRIPTS_PATH
from ufotest.util import (execute_command,
                          setup_environment,
                          init_install,
                          check_install,
                          execute_script,
                          get_version,
                          get_path,
                          check_vivado,
                          check_path)
from ufotest.install import (install_dependencies,
                             install_fastwriter,
                             install_pcitools,
                             install_libufodecode,
                             install_libuca,
                             install_uca_ufo,
                             install_ipecamera)
from ufotest.camera import save_frame, import_raw, set_up_camera, tear_down_camera
from ufotest.testing import TestRunner, TestContext, TestReport
from ufotest.ci.build import BuildRunner, build_context_from_config
from ufotest.ci.server import server, BuildWorker


CONFIG = Config()


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='Print the version of the program')
def cli(version):
    if version:
        version = get_version()
        click.secho('UFOTEST VERSION')
        click.secho(version, bold=True)
        return 0


@click.command('install', short_help='Install the project and its dependencies')
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
@click.option('--verbose', '-v', is_flag=True, help='Show additional console output')
@click.option('--no-dependencies', '-d', is_flag=True, help='Skip installation of required system packages')
@click.option('--no-libuca', '-l', is_flag=True, help='Skip installation of libuca')
@click.option('--no-vivado', is_flag=True, help='Skip installation of vivado')
def install(path, verbose, no_dependencies, no_libuca, no_vivado):
    """
    Installing the Project into PATH

    PATH will be the system path, which will then contain subfolders with all the required repositories and
    dependencies
    """
    if not check_install():
        return 1

    path = os.path.realpath(path)

    operating_system = CONFIG['install']['os']
    click.secho('\n| | STARTING INSTALLATION | |', bold=True)
    click.secho('--| Configured OS: {}'.format(operating_system))
    click.secho('--| Configured package install: {}'.format(CONFIG['install'][operating_system]['package_install']))
    click.secho('--| Camera dimensions: {} x {}'.format(
        CONFIG.get_sensor_width(),
        CONFIG.get_sensor_height()
    ))

    if not no_dependencies:
        click.secho('\n=====| Installing System Packages |=====', bold=True)
        install_dependencies(verbose=verbose)
    else:
        click.secho('\n=====| Skipping Dependencies |=====', bold=True)

    click.secho('\n=====| Installing fastwriter |=====', bold=True)
    install_fastwriter(path, verbose=verbose)

    click.secho('\n=====| Installing pcitools |=====', bold=True)
    install_pcitools(path, verbose=verbose)

    click.secho('\n=====| Installing libufodecode |=====', bold=True)
    install_libufodecode(path, verbose=verbose)

    if not no_libuca:
        click.secho('\n=====| Installing Libuca |=====', bold=True)
        install_libuca(path, verbose=verbose)

        click.secho('\n=====| Installing uca-ufo |=====', bold=True)
        install_uca_ufo(path, verbose=verbose)

        click.secho('\n=====| Installing ipecamera plugin |=====', bold=True)
        install_ipecamera(path, verbose)
    else:
        click.secho('\n=====| Skipping Libuca |=====', bold=True)
    return 0


@click.command('init', short_help='Initializes the installation folder and config file for the app')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.option('--force', '-f', is_flag=True, help='Deletes the current installation to reinstall')
def init(verbose, force):
    """Initializes the installation folder for this application. This folder will be located at *$HOME/.ufotest*.
    This init includes the creation of the necessary folder structure for the archive and the tests, as well as the
    creation of the config file from a default template.
    """
    installation_path = get_path()
    click.secho('\n| | INITIALIZING UFOTEST INSTALLATION | |', bold=True)
    click.secho('--| installation path: {}'.format(installation_path))

    if check_path(installation_path, is_dir=True):
        if force:
            shutil.rmtree(get_path())
            click.secho('(+) Deleted old installation folder!', fg='green')
        else:
            click.secho('[!] An installation folder already exists!', fg='red')
            click.secho('    Please use the --force flag if you wish to replace the existing installation')
            sys.exit(1)
    else:
        click.secho('    Installation folder does not yet exist')

    init_install(verbose=verbose)
    click.secho('(+) UfoTest app is initialized!', bold=True, fg='green')

    sys.exit(0)


@click.command('config', short_help='Edit the config for ufotest')
@click.option('--editor', '-e', type=click.STRING, help='Specify the editor command to be used to open the config file')
def config(editor):
    """
    Edit the configuration file for this project
    """
    if not check_install():
        return 1

    config_path = get_config_path()
    click.edit(filename=config_path, editor=editor)

    return 0


@click.command('frame', short_help='Acquire and display a frame from the camera')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.option('--output', '-o', type=click.STRING,
              help='Specify the output file path for the frame', default='/tmp/frame.raw')
@click.option('--display', '-d', is_flag=True, help='display the frame in seperate window')
def frame(verbose, output, display):
    """
    Capture a frame from the camera and display it to the user
    """

    if not check_install():
        return 1

    # Setup all the important environment variables and stuff
    setup_environment()

    execute_command('rm /tmp/frame*', verbose)
    if verbose:
        click.secho('Removed the previous frame buffer', fg='green')

    # Call the necessary pci commands
    save_frame(output, verbose=verbose)

    # Display the file using matplot lib
    if display:
        images = import_raw(
            path=output,
            n=1,
            sensor_height=CONFIG.get_sensor_height(),
            sensor_width=CONFIG.get_sensor_width()
        )

        import matplotlib.pyplot as plt
        matplotlib.use('TkAgg')

        plt.imshow(images[0])
        plt.show()

    return 0


@click.command('script', short_help="Execute one of the known (bash) scripts")
@click.argument('name', type=click.STRING)
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
def script(name, verbose):
    """Executes a registered script with the given NAME
    """
    if not check_install():
        return 1

    exit_code = execute_script(name, verbose=verbose)
    if not exit_code:
        click.secho('Script "{}" succeeded'.format(name), bold=True, fg='green')
    else:
        click.secho('Script "{}" failed'.format(name), bold=True, fg='red')


@click.command('list-scripts', short_help='List all available scripts')
def list_scripts():
    if not check_install():
        return 1

    click.secho('The following scripts are available:\n', fg='green', bold=True)

    for script_id, script_data in SCRIPTS.items():
        click.secho(script_id, bold=True)
        click.secho('   Path: {}\n   Description: {}\n   Author: {}\n'.format(
            script_data['path'],
            script_data['description'],
            script_data['author']
        ))


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
def flash(verbose, file: str):
    """
    Flashes a given ".bit" FILE to the internal memory of the fpga

    FILE will be the string path of the file to be used for the flashing process
    """
    if not check_install():
        return 1

    # -- ECHO CONFIGURATION
    click.secho('\n| | FLASHING THE FPGA MEMORY | |', bold=True)
    click.secho('--| bitfile: {}\n'.format(file))

    # -- CHECKING IF THE GIVEN FILE EVEN EXISTS
    file_path = os.path.abspath(file)
    file_exists = check_path(file_path, is_dir=False)
    if not file_exists:
        click.secho('[!] The given path does not exist!', fg='red')
        return 1

    # -- CHECKING IF THE FILE EVEN IS A BIT FILE
    file_extension = file_path.split('.')[-1].lower()
    is_bit_file = file_extension == 'bit'
    if not is_bit_file:
        click.secho('[!] The given file is not a .BIT file', fg='red')
        return 1

    # -- CHECKING IF VIVADO IS INSTALLED
    vivado_installed = check_vivado()
    if not vivado_installed:
        click.secho('[!] Vivado is not installed, please install Vivado to be able to flash the fpga!', fg='red')
        return 1
    elif verbose:
        click.secho('    Vivado installation found')

    # -- STARTING VIVADO SETTINGS
    vivado_command = CONFIG['install']['vivado_settings']
    execute_command(vivado_command, verbose, cwd=os.getcwd())
    click.secho('    Finished setup of vivado environment')

    # -- FLASHING THE BIT FILE
    flash_command = "{command} -nolog -nojournal -mode batch -source fpga_conf_bitprog.tcl -tclargs {file}".format(
        command=CONFIG['install']['vivado_command'],
        file=file_path
    )
    exit_code = execute_command(flash_command, verbose, cwd=SCRIPTS_PATH)
    if not exit_code:
        click.secho('(+) Flashed FPGA with: {}'.format(file_path), fg='green', bold=True)
        return 0
    else:
        return 1


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
    if not check_install():
        return 1

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
        return 1

    if verbose:
        click.secho(test_report.to_string())

    click.secho('(+) Test report saved to: {}'.format(test_context.folder_path), fg='green', bold=True)
    click.secho('    View the report at: http://localhost/archive/{}/report.html'.format(test_context.folder_name))

    return 0


@click.group('ci', short_help='continuous integration related commands')
def ci():
    pass


@click.command('build', short_help='Applies newest commit from remote repository and then executes test suite')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.argument('suite', type=click.STRING)
def build(verbose, suite):
    """
    Start a new CI build process using the test suite SUITE.
    """
    # -- ECHO CONFIGURATION
    click.secho('\n| | INTEGRATING REMOTE REPOSITORY | |', bold=True)
    click.secho('--| Repository url: {}'.format(CONFIG.get_ci_repository_url()))
    click.secho('--| Repository branch: {}'.format(CONFIG.get_ci_branch()))
    click.secho('--| Bitfile relative path: {}'.format(CONFIG.get_ci_bitfile_path()))
    click.secho('--| Test suite: {}\n'.format(suite))

    # -- RUNNING THE PROCESS
    with build_context_from_config(CONFIG) as build_context:
        # The "build_context_from_config" function builds the context object entirely on the basis of the configuration
        # file, which means, that it also uses the default test suite defined there. Since the build function is meant
        # to be able to pass the test suite as a parameter, we will have to overwrite this piece of config manually.
        build_context.test_suite = suite

        build_runner = BuildRunner(build_context)
        build_report = build_runner.build()
        build_report.save(build_context.folder_path)


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

# Registering the commands within the click group
cli.add_command(init)
cli.add_command(config)
cli.add_command(install)
cli.add_command(script)
cli.add_command(frame)
cli.add_command(setup)
cli.add_command(teardown)
cli.add_command(list_scripts)
cli.add_command(flash)
cli.add_command(test)
cli.add_command(ci)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
