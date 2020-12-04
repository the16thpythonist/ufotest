import os

from flask import Flask, request, send_from_directory
from flask_restful.reqparse import RequestParser

from ufotest.config import get_path


PATH = get_path()
ARCHIVE_PATH = os.path.join(PATH, 'archive')
server = Flask('UfoTest CI Server')


@server.route('/push', methods=['POST'])
def push():
    print(request.get_json())
    parser = RequestParser()
    parser.parse_args()


@server.route('/archive/<path:path>')
def archive(path):
    return send_from_directory(ARCHIVE_PATH, path)
