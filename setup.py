#!/usr/bin/env python
"""The setup script."""
import os
import shutil
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.install import install


class CustomInstallCommand(install):

    def run(self):
        # Checking if the ".ufotest" folder exists within the HOME folder of the user and if
        # it does not exist it will be added

        # home_path = str(Path.home())
        # path = os.path.join(home_path, '.ufotest')
        # print('Checking for the existence of the path "{}"...'.format(path))
        # if os.path.exists(path):
        #     print('-> Path exists, skipping')
        # else:
        #     os.makedirs(path)
        #     print('-> Created folder "{}"'.format(path))

        install.run(self)


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read()

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    cmdclass={
        'install': CustomInstallCommand
    },
    author="Jonas Teufel",
    author_email='jonseb1998@gmail.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="CLI for setting up ufo camera test station",
    entry_points={
        'console_scripts': [
            'ufotest=ufotest.cli:cli',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='ufotest',
    name='ufotest',
    packages=find_packages(include=['ufotest', 'ufotest.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/the16thpythonist/ufotest',
    version='0.5.1',
    zip_safe=False,
)
