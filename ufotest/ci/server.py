import os
import subprocess
from multiprocessing import Process

from flask import Flask, request, send_from_directory, jsonify

from ufotest.config import Config, get_path
from ufotest.ci.util import build_repository, is_building
from ufotest.ci.build import BuildLock, BuildRunner, build_context_from_request


CONFIG = Config()
PATH = get_path()
ARCHIVE_PATH = os.path.join(PATH, 'archive')
server = Flask('UfoTest CI Server')


@server.route('/', methods=['GET'])
def home():
    return 'Hello there! I am the CI server for the ufotest application!', 200


@server.route('/push/github', methods=['POST'])
def push():
    data = request.get_json()

    if is_building():
        # error code 423 represents the fact that the resource which is being requested is locked. I think this best
        # represents what is going on. There cannot be two simultaneous processes because both of them would be trying
        # to access the same hardware. This is why a request will be rejected if another build process is
        # currently running.
        return 'A build process is currently in progress!', 423

    def build(_data):
        with build_context_from_request(_data) as build_context:
            build_runner = BuildRunner(build_context)
            build_report = build_runner.build()
            build_report.save(build_context.folder_path)

    process = Process(target=build, args=(data, ))
    process.start()

    return 'New build process was initiated', 200

    test_suite = CONFIG.get_ci_suite()
    # Here we are using subprocess.Popen instead of the subprocess.run command as it is used in the utility function
    # 'execute_command' because that is a higher level implementation which will always wait for the process to finish.
    # in this case however we want to explicitly start the command as a backround process because we want to deliver
    # the http response as quickly as possible. This cant wait the several minutes which are required for the whole
    # build process...
    command = "ufotest ci run {}".format(test_suite)
    subprocess.Popen(command, shell=True, stdout=None, stdin=None)

    return 'New build process was initiated', 200


@server.route('/archive/<path:path>')
def archive(path):
    return send_from_directory(ARCHIVE_PATH, path)
