import os
import json
import time
import smtplib
import datetime
import shutil

import click
from flask import Flask, request, send_from_directory, jsonify

from ufotest.config import Config, get_path
from ufotest.util import get_template, get_version
from ufotest.util import cerror, cprint, cresult
from ufotest.util import get_build_reports, get_test_reports
from ufotest.util import get_folder_size, format_byte_size
from ufotest.exceptions import BuildError
from ufotest.camera import UfoCamera
from ufotest.ci.build import BuildQueue, BuildLock, BuildRunner, BuildReport, build_context_from_request
from ufotest.ci.mail import send_report_mail

CONFIG = Config()
PATH = get_path()

ARCHIVE_PATH = os.path.join(PATH, 'archive')
BUILDS_PATH = os.path.join(PATH, 'builds')
STATIC_PATH = os.path.join(PATH, 'static')


class BuildAdapterGitlab(object):

    def __init__(self, data: dict):
        self.data = data

    def get(self):
        build = {
            'repository': {
                'name': self.data['repository']['name'],
                'clone_url': self.data['repository']['git_http_url'],
                'owner': {
                    'name': self.data['user_name'],
                    'email': self.data['user_email']
                }
            },
            'ref': self.data['ref'],
            'pusher': self.get_pusher(),
            'commits': self.get_commits()
        }

        return build

    def get_pusher(self) -> dict:
        last_commit_data = self.data['commits'][-1]
        return last_commit_data['author']

    def get_commits(self) -> list:
        return [commit_data['id'] for commit_data in self.data['commits'][::-1]]


class BuildWorker(object):
    """
    This class wraps the main loop which is responsible for actually executing the build jobs.

    This class was designed so that it's run method could essentially be used as the main loop of an entirely different
    subprocess. Its main loop periodically checks the build queue for the case that new build jobs have arrived over
    the web server.

    **The build data**

    So the basic way the build queue works is that the web server receives a new build job in the form of a json data
    structure. This data structure is then put into the build queue until it is popped out again by this worker process.
    To understand the build process it is important to understand how this json data from the build queue is structured.
    The most important parts are explained here:

    - repository
        - owner
            - *email*: The string email address of the owner of the repository. This will be used to send a report mail
              to the owner whenever a build has finished.
            - *name*: The string name of the owner of the repo. This is used to correctly address the person in the mail
        - *clone_url*: The string url with which the repository can be cloned. This is then used to actually clone the
          repository to flash the most recent changes to the camera.
    - pusher
        - *email*: The string email address of the person which caused the most recent push to the repository.
        - *name*: The string name of the pusher
    - *ref*: A string with the branch name to which the commit was issued. For the ufotest application only a certain
      branch is being monitored. This will be used to check if the changes have actually occurred on the relevant branch
    - *commits*: A list of strings, where each string is the string identifier for one of the commits for the
      repository. The last one will be used as the string to checkout and use as the basis for the tests.

    This should have been committed
    """
    def __init__(self):
        self.running = True

    def run(self):
        try:
            while self.running:
                time.sleep(1)

                if not BuildQueue.is_empty() and not BuildLock.is_locked():
                    build_request = BuildQueue.pop()

                    try:
                        # ~ RUN THE BUILD PROCESS
                        build_report = self.run_build(build_request)  # raises: BuildError

                        # ~ SEND REPORT MAILS
                        # After the build process has terminated we want to inform the relevant people of the outcome.
                        # This is mainly Two people: The maintainer of the repository is getting an email and pusher
                        self.send_report_mails(build_request, build_report)

                    except BuildError as error:
                        cerror('The build process was terminated due to a build error!')
                        cerror(str(error))

                    except smtplib.SMTPAuthenticationError as error:
                        cerror('The email credentials provided in the config file were not accepted by the server!')
                        cerror(str(error))

                    except OSError as error:
                        cerror('Report mails could not be sent because there is no network connection')
                        cerror(str(error))

        except KeyboardInterrupt:
            cprint('\n...Stopping BuildWorker')

    def run_build(self, build_request: dict) -> BuildReport:
        """Actually runs the build process based on the information in *build_request* and returns the build report.

        :param build_request: A dict, which specifies the request, that triggered the build.

        :raises BuildError: If there is an error during the build process. All kinds of exceptions are wrapped as
            this kind of error, so this is the only thing, one has to worry about
        """
        # ~ ACTUALLY BUILD
        with build_context_from_request(build_request) as build_context:  # raises: BuildError
            build_runner = BuildRunner(build_context)
            build_runner.run(test_only=True)
            build_report = BuildReport(build_context)
            build_report.save(build_context.folder_path)

            return build_report

    def send_report_mails(self, build_request: dict, build_report: BuildReport) -> None:
        """Sends the report mails with the results of *build_report* to recipients based on the *build_request*

        :param build_request: A dict, which specifies the request, that triggered the build.
        :param build_report: The BuildReport which was generated from the build process.

        :raises smtplib.SMTPAuthenticationError: If the username and password configured within the config file are not
            accepted by the SMTPServer
        :raises OSError: If there is no connection to the mail server.
        """
        maintainer_email = build_request['repository']['owner']['email']
        maintainer_name = build_request['repository']['owner']['name']
        send_report_mail(maintainer_email, maintainer_name, build_report)

        pusher_email = build_request['pusher']['email']
        pusher_name = build_request['pusher']['name']
        send_report_mail(pusher_email, pusher_name, build_report)


server = Flask('UfoTest CI Server', static_folder=None)


@server.route('/', methods=['GET'])
def home():
    """
    This method returns the HTML content which will display the home page for the ufotest web interface.
    On default the home page consists of various informative panels, which show the current state of the ufotest
    project, the current installation, the current hardware and a list for both the most recent builds and the most
    recent test reports.

    :return: The rendered string HTML template
    """
    template = get_template('home.html')
    template = CONFIG.pm.apply_filter('home_template', template)

    # The integer amount of how many items to be shown for both the most recent test and most recent build reports.
    recent_count = CONFIG.pm.apply_filter('home_recent_count', 5)

    test_reports = get_test_reports()

    recent_builds = get_build_reports()[:recent_count]
    recent_tests = test_reports[:recent_count]

    # So we derive the summary values about the state of the hardware and firmware from the most recent test report. On
    # default the test reports returned by "get_test_reports" are sorted by recentness, which would mean that we would
    # only need to get the first item from the respective list. BUT, a filter hook applies to the return value of these
    # functions which could mean that possibly a filter is applied which changes the ordering, so to be sure that this
    # is the most recent one, we sort it again.
    if len(recent_tests) != 0:
        most_recent_test_report = sorted(recent_tests, key=lambda d: d['start_iso'], reverse=True)[0]

    if len(recent_builds) != 0:
        most_recent_build_report = sorted(recent_builds, key=lambda d: d['start_iso'], reverse=True)[0]

    camera_class = CONFIG.pm.apply_filter('camera_class', UfoCamera)
    camera = camera_class(CONFIG)

    status_summary = [
        # UFOTEST INFORMATION
        {
            'id': 'ufotest-version',
            'label': 'UfoTest Version',
            'value': get_version()
        },
        {
            'id': 'installation-folder',
            'label': 'Installation Folder',
            'value': CONFIG.get_path()
        },
        {
            'id': 'report-count',
            'label': 'Total Test Reports',
            'value': len(test_reports)
        },
        {
            'id': 'loaded-plugins',
            'label': 'Loaded Plugins',
            'value': len(CONFIG.pm.plugins)
        },
        False,
        {
            'id': 'repository',
            'label': 'Source Repository',
            'value': f'<a href="{CONFIG.get_repository_url()}">GitHub</a>'
        },
        {
            'id': 'documentation',
            'label': 'Project Documentation',
            'value': f'<a href="{CONFIG.get_documentation_url()}">ReadTheDocs</a>'
        },
        False,
        # FIRMWARE / BUILD INFORMATION
        {
            'id': 'firmware-version',
            'label': 'Firmware Version',
            'value': '1.0'
        },
        {
            'id': 'recent-build',
            'label': 'Recent Build',
            'value': most_recent_build_report['start_iso'] if len(recent_builds) != 0 else 'No build yet'
        },
        # HARDWARE INFORMATION
        False,
        {
            'id': 'camera-class',
            'label': 'Camera Class',
            'value': str(camera_class.__name__)
        },
        {
            'id': 'available',
            'label': 'Camera Available',
            'value': f'<i class="fas fa-circle {"green" if camera.poll() else "red"}"> </i>'
        },
        {
            'id': 'hardware-version',
            'label': 'Hardware Version',
            'value': camera.get_prop('hardware_version')
        },
        {
            'id': 'sensor-dimensions',
            'label': 'Sensor Dimensions',
            'value': f'{CONFIG.get_sensor_width()} x {CONFIG.get_sensor_height()}'
        },
        {
            'id': 'sensor-version',
            'label': 'Sensor Version',
            'value': camera.get_prop('sensor_version')
        }
    ]
    status_summary = CONFIG.pm.apply_filter('home_status_summary', status_summary)

    # ~ CALCULATING DISK USAGE
    # TODO: The unit is hardcoded. This could be part of the config. Super low prio though
    used_space = get_folder_size(CONFIG.get_path())

    # https://stackoverflow.com/questions/48929553/get-hard-disk-size-in-python
    _, _, free_space = shutil.disk_usage('/')

    context = {
        'status_summary':       status_summary,
        'recent_builds':        recent_builds,
        'recent_tests':         recent_tests,
        # 13.09.2021: I decided that displaying the amount of used space would be a good idea for the home screen,
        # because now the complete source repo content is saved for each build report and depending how large the
        # source repo is (gigabytes?) This could fill up the disk rather quickly...
        'used_space':           used_space,
        'free_space':           free_space
    }

    return template.render(context), 200


@server.route('/config', methods=['GET'])
def config():
    template = get_template('config.html')

    with open(get_path('config.toml')) as config_file:
        config_lines = config_file.readlines()
        context = {
            'line_count':       len(config_lines),
            'config_content':   ''.join(config_lines)
        }

    return template.render(context), 200


@server.route('/config/save', methods=['POST'])
def save_config():
    try:
        data = request.get_json()
        content = data['content']
        with open(get_path('config.toml'), mode='w') as config_file:
            config_file.write(content)
        return 'Config file saved', 200

    except:
        return 'There has been an error', 400


@server.route('/push/github', methods=['POST'])
def push_github():
    data = request.get_json()

    BuildQueue.push(data)

    return 'New build added to the queue', 200


@server.route('/push/gitlab', methods=['POST'])
def push_gitlab():
    data = request.get_json()

    try:
        adapter = BuildAdapterGitlab(data)
        BuildQueue.push(adapter.get())
    except Exception as e:
        msg = '[!] An error occurred while pushing a gitlab request into the build queue: {}'.format(str(e))
        click.secho(msg, fg='red')

    return 'New build added to the queue', 200


@server.route('/archive')
def archive_list():
    reports = []
    for root, folders, files in os.walk(ARCHIVE_PATH):
        for folder in folders:
            folder_path = os.path.join(root, folder)
            report_json_path = os.path.join(folder_path, 'report.json')

            # We really need to check for the existence here because of the following case: A test run has been started
            # but is not yet complete. In this case the test folder already exists, but the report does not. In this
            # case attempting to open the file would cause an exception!
            if os.path.exists(report_json_path):
                with open(report_json_path, mode='r') as report_json_file:
                    report = json.loads(report_json_file.read())
                    reports.append(report)

        break

    sorted_reports = sorted(
        reports,
        key=lambda r: datetime.datetime.fromisoformat(r['start_iso']),
        reverse=True
    )

    template = get_template('archive_list.html')
    return template.render({'reports': sorted_reports}), 200


@server.route('/archive/<path:path>')
def archive_detail(path):
    return send_from_directory(ARCHIVE_PATH, path)


@server.route('/builds')
def builds_list():
    reports = []
    for root, folders, files in os.walk(BUILDS_PATH):
        for folder in folders:
            folder_path = os.path.join(root, folder)
            report_json_path = os.path.join(folder_path, 'report.json')

            if os.path.exists(report_json_path):
                with open(report_json_path, mode='r') as report_json_file:
                    report = json.loads(report_json_file.read())
                    reports.append(report)

        break

    sorted_reports = sorted(
        reports,
        key=lambda r: datetime.datetime.fromisoformat(r['start_iso']),
        reverse=True
    )

    template = get_template('builds_list.html')
    return template.render({'reports': sorted_reports}), 200


@server.route('/builds/<path:path>')
def builds_detail(path):
    return send_from_directory(BUILDS_PATH, path)


@server.route('/static/<path:path>')
def static(path):
    return send_from_directory(STATIC_PATH, path)


@server.route('/favicon.ico')
def favicon():
    return send_from_directory(STATIC_PATH, 'favicon.ico')
