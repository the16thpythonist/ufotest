import os
import json
import time

from flask import Flask, request, send_from_directory, jsonify

from ufotest.config import Config, get_path
from ufotest.util import get_template
from ufotest.ci.build import BuildQueue, BuildLock, BuildRunner, build_context_from_request
from ufotest.ci.mail import send_report_mail

CONFIG = Config()
PATH = get_path()

ARCHIVE_PATH = os.path.join(PATH, 'archive')
BUILDS_PATH = os.path.join(PATH, 'builds')
STATIC_PATH = os.path.join(PATH, 'static')


class BuildWorker(object):

    def __init__(self):
        self.running = True

    def run(self):
        while self.running:
            time.sleep(1)

            if not BuildQueue.is_empty() and not BuildLock.is_locked():
                build = BuildQueue.pop()

                self.execute_build(build)

    def execute_build(self, build: dict):

        # -- ACTUALLY BUILD
        with build_context_from_request(build) as build_context:
            build_runner = BuildRunner(build_context)
            build_report = build_runner.build()
            build_report.save(build_context.folder_path)

        # -- SEND REPORT MAILS
        # After the build process has terminated we want to inform the relevant people of the outcome. This is mainly
        # Two people: The maintainer of the repository is getting an email and the person which actually issued the
        # push is getting an email.
        maintainer_email = build['repository']['owner']['email']
        maintainer_name = build['repository']['owner']['name']
        send_report_mail(maintainer_email, maintainer_name, build_report)

        pusher_email = build['pusher']['email']
        pusher_name = build['pusher']['name']
        send_report_mail(pusher_email, pusher_name, build_report)


server = Flask('UfoTest CI Server', static_folder=None)

@server.route('/', methods=['GET'])
def home():
    template = get_template('home.html')
    return template.render({}), 200


@server.route('/push/github', methods=['POST'])
def push():
    data = request.get_json()

    BuildQueue.push(data)

    return 'New build added to the queue', 200


@server.route('/archive')
def archive_list():
    reports = []
    for root, folders, files in os.walk(ARCHIVE_PATH):
        for folder in folders:
            folder_path = os.path.join(root, folder)
            report_json_path = os.path.join(folder_path, 'report.json')
            with open(report_json_path, mode='r') as report_json_file:
                report = json.loads(report_json_file.read())
                reports.append(report)

        break

    template = get_template('archive_list.html')
    return template.render({'reports': reports}), 200


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
            with open(report_json_path, mode='r') as report_json_file:
                report = json.loads(report_json_file.read())
                reports.append(report)

        break

    template = get_template('builds_list.html')
    return template.render({'reports': reports}), 200


@server.route('/builds/<path:path>')
def builds_detail(path):
    return send_from_directory(BUILDS_PATH, path)


@server.route('/static/<path:path>')
def static(path):
    return send_from_directory(STATIC_PATH, path)
