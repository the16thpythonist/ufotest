import os
import json
import time
import smtplib
import datetime

import click
from flask import Flask, request, send_from_directory, jsonify

from ufotest.config import Config, get_path
from ufotest.util import get_template
from ufotest.util import cerror, cprint, cresult
from ufotest.exceptions import BuildError
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
    template = get_template('home.html')
    return template.render({}), 200


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
