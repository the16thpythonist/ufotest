from ufotest.config import CONFIG


PACKAGES = {
    'ubuntu': [
        'python2',
        'python2-dev',
        'swig'
    ],
    'suse': [
        'cmake',
        'python2',
        'python2-devel',
        'swig',
        'uthash-devel',
        'libxml',
        'libxml-devel',
        'uuid-devel',
        'xfsprogs-devel'
    ]
}


def install_package(package_name: str):
    package_install_command = CONFIG['install']['package_install']

    command = '{} {}'.format(package_install_command, package_name)
    pass

def print_hello():
    print("HELLO")
