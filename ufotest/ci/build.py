from __future__ import annotations
import os
import click
import datetime
import shutil
from contextlib import AbstractContextManager
from typing import Optional

from ufotest.config import Config, get_path, get_builds_path
from ufotest.util import AbstractRichOutput, get_repository_name, execute_command, get_command_output, get_template
from ufotest.testing import TestRunner, TestReport


UFOTEST_PATH = get_path()
BUILDS_PATH = get_builds_path()


# FUNCTIONS

def build_context_from_config(config: Config) -> BuildContext:
    """Creates a new BuildContext instance from the provided *config*.

    This function is mainly for the purpose of a manual build trigger. For manually triggering a build there
    obviously is no request data from which to get the repo url / commit hash from, which is why it will use the
    information which were defined in the config file.

    :return: The build context which was based on the information in the config file in the ufotest folder
    """
    repository_url = config.get_ci_repository_url()
    repository_branch = config.get_ci_branch()
    repository_commit = 'FETCH_HEAD'
    test_suite = config.get_ci_suite()

    return BuildContext(
        repository_url,
        repository_branch,
        repository_commit,
        test_suite
    )


def build_context_from_request(data: dict) -> BuildContext:
    """Creates a new BuildContext instance from given json payload *data* from the github web hook request.

    This function extracts the information about which commit to clone from which repo from the given payload of the
    request.

    :return: the build context instance.
    """
    repository_url = data['repository']['clone_url']
    repository_branch = data['ref'].replace('refs/heads/', '')
    repository_commit = data['commits'][-1]

    config = Config()
    test_suite = config.get_ci_suite()

    return BuildContext(
        repository_url,
        repository_branch,
        repository_commit,
        test_suite
    )


# CLASSES

class BuildLock(object):
    """This is a static class which models a persistent lock, which keeps multiple build processes from running at the
    same time.

    **Why?**
    So first of all why is this important. The ci server of ufotest accepts request which are generated by github
    web hooks, whenever new code is pushed to source repository. As a response to such a push, a new build process is
    initiated. So assuming the case that there would be two separate pushes to the repo in quick succession. This
    would cause a second python process to attempt to start a build process before the first one is done. The build
    process interfaces with the actual camera hardware. Having two processes attempt to send commands to the same
    hardware would result in errors. Thus, the ufotest app has to be restricted to only one build process at a time.

    **How?**
    This static class implements this locking functionality by providing the 'acquire' and 'release' methods. With
    these a indicator file 'build.locked' is saved to the installation folder of the ufotest installation. As long as
    this file exists, this locks status will be blocking. The release method simply removes this file again.
    """
    LOCK_PATH = os.path.join(UFOTEST_PATH, 'build.locked')

    @classmethod
    def acquire(cls):
        """Acquires the lock for the process which calls this method.

        If the lock is already locked by another process, this method will raise an error.

        :raise PermissionError: If another build process has already acquired the lock.
        """
        if cls.is_locked():
            raise PermissionError('Another build process is currently already running')
        else:
            with open(cls.LOCK_PATH, mode='w') as lock_file:
                lock_file.write('True')

    @classmethod
    def release(cls):
        """Releases the locK again, so that other processes can start build processes in the future.

        :return: void
        """
        os.remove(cls.LOCK_PATH)

    @classmethod
    def is_locked(cls) -> bool:
        """Returns the boolean value of whether or not the lock is currently locked by some process.

        If the lock is indeed locked, this would mean that currently there is a build process running.

        :return: a boolean
        """
        return os.path.exists(cls.LOCK_PATH)


class BuildContext(AbstractContextManager):
    """Represents the context of a build process. The context in this case refers to all necessary information about
    and around the build process. Objects of this context class will save all the information about the build process
    and manage all the secondary processes which are involved with a build process such as the acquisition of the lock
    and the creation of the build archive folder. But the actual build process is NOT the responsibility of this class!

    **Context Manager**

    This class is a python context manager, which means that it implements the __enter__ and __exit__ magic methods and
    can be used with the 'with' keyword.
    The __enter__ of the context acquires the build lock for the current process and creates the correct folder within
    the 'builds' archive.
    The __exit__ of the context releases the lock again and deletes the folder of the actual cloned repo.
    It is important that both these functions actually get called, which is why this class should absolutely be used
    in combination with the 'with' keyword!

    .. code-block:: python

        with BuildContext(*args) as context:
            # only here the context should actually be used!

    """
    def __init__(self, repository_url: str, branch_name: str, commit_name: str, test_suite: str):
        self.repository_url = repository_url
        self.branch = branch_name
        self.commit = commit_name
        self.test_suite = test_suite

        self.config = Config()
        self.creation_datetime = datetime.datetime.now()

        # derived attributes
        self.repository_name = get_repository_name(repository_url)
        self.repository_path = os.path.join(UFOTEST_PATH, self.repository_name)
        self.folder_name = '{}__{}'.format(
            self.repository_name,
            self.creation_datetime.strftime('%Y_%m_%d__%H_%M')
        )
        self.folder_path = os.path.join(BUILDS_PATH, self.folder_name)

        # non initialized attributes
        # These are the attributes, which have to be declared, but which cannot be initialized in the constructor.
        # The start and end time of course can only be acquired during the actual start and end.
        # The bitfile path actually has to be set by the BuildRunner. It is not known in before hand! The test report
        # as well can obviously only be added after the actual test are done.
        self.start_datetime: Optional[datetime.datetime] = None
        self.end_datetime: Optional[datetime.datetime] = None
        self.bitfile_path = None
        self.test_report: Optional[TestReport] = None

    # IMPLEMENT 'AbstractContextManger'

    def __enter__(self) -> BuildContext:
        """Magic method which gets called whenever the context manager is entered. Returns the context manager instance.

        This method gets called whenever the context is entered. It manages two important responsibilities in
        preparation for the build process:

        - It acquires the build lock for the current process.
        - It creates the according folder for the build process within the 'builds' archive.

        :raise PermissionError: If another build process is currently running.

        :return: The object instance of BuildContext on which this method was invoked
        """
        # -- ACQUIRING THE LOCK
        # So the BuildLock is a static class which models a *persistent* lock which is supposed to prevent multiple
        # parallel build processes to be running at the same time. Since there is only one hardware every process would
        # try to interface with, this would be a bad idea. I also contemplated whether I should already acquire the
        # lock here or during the actual build process. The final knockout argument was that since i am creating the
        # folder here, if the lock acquisition failed later on, the folder would still be created and that would not be
        # the behaviour we want.
        BuildLock.acquire()

        # -- CREATING THE BUILD FOLDER
        os.mkdir(self.folder_path)

        # -- RECORDING THE START TIME
        self.start_datetime = datetime.datetime.now()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Magic method which gets called whenever the context is left again.

        This method gets called whenever the context is being closed. It manages two important responsibilities for
        finalizing the build process:

        - It releases the build lock
        - It deletes the folder of the cloned repository, so that the next process can perform an entirely new clone
          process.

        :return: void
        """
        # -- DELETING THE CLONED REPOSITORY
        # another important thing to do to be able to have another build process be able to run again is to delete the
        # folder which was used for the cloning process.
        shutil.rmtree(self.repository_path)

        # -- RELEASING THE LOCK
        # By doing this, another build process is now able to be started again in a different process possibly
        BuildLock.release()


class BuildReport(AbstractRichOutput):
    """This class represents a report, which is being created as the result of a build process. A build report contains
    information and metrics about the build process which are important to provide to the users.

    *Rich Output*

    This class implements the abstract base class AbstractRichOutput, which means that it can be converted to various
    formats, which include markdown and html. These can be saved to files to later be reviewed by a user.
    """
    DATETIME_FORMAT = '%d.%m %Y, %H:%M'

    def __init__(self, build_context: BuildContext):
        self.context = build_context

        # Derived
        self.start = self.context.start_datetime.strftime(self.DATETIME_FORMAT)
        self.end = self.context.end_datetime.strftime(self.DATETIME_FORMAT)
        duration_time_delta = self.context.end_datetime - self.context.start_datetime
        self.duration = round(duration_time_delta.seconds / 60)
        self.repository = self.context.repository_url
        self.repository_name = self.context.repository_name
        self.branch = self.context.branch
        self.commit = self.context.commit
        self.folder = self.context.folder_path
        self.folder_name = os.path.basename(self.folder)
        self.bitfile_path = self.context.bitfile_path
        self.bitfile_name = os.path.basename(self.bitfile_path)
        self.test_suite = self.context.test_suite
        self.test_count = self.context.test_report.test_count
        self.test_percentage = self.context.test_report.success_ratio

    def save(self, folder_path: str):
        """Saves the both the MD and HTML version of the report into the given *folder_path*.

        :return: void
        """
        # -- SAVE MARKDOWN FILE
        markdown_path = os.path.join(folder_path, 'report.md')
        with open(markdown_path, mode='w') as markdown_file:
            markdown_file.write(self.to_markdown())

        # -- SAVE HTML FILE
        html_path = os.path.join(folder_path, 'report.html')
        with open(html_path, mode='w') as html_file:
            html_file.write(self.to_html())

        click.secho('(+) Build report saved to: {}'.format(folder_path), fg='green')

    def __str__(self):
        return self.to_string()

    # IMPLEMENT 'AbstractRichOutput'

    def to_markdown(self) -> str:
        template = get_template('build_report.md')
        return template.render({'report': self})

    def to_latex(self) -> str:
        # not important right now
        pass

    def to_string(self) -> str:
        template = get_template('build_report.text')
        return template.render({'report': self})

    def to_html(self) -> str:
        template = get_template('build_report.html')
        return template.render({'report': self})


class BuildRunner(object):
    """This class is responsible for actually executing the build process.

    This build process involves the following individual steps:

    - The remote git repository is cloned to the local system and checked out to the desired branch/commit.
    - The actual bit file is extracted from this repo.
    - This bit file is being used to flash the new configuration to the fpga board.
    - Finally the desired test suite is being run with this new hardware version.

    A new BuildRunner object needs to be constructed with an appropriate BuildContext object as an argument. This is
    because the context object contains all the necessary information about *how* the build process is supposed to work
    in terms of which repo to clone, which test suite to run etc.

    **Example**

    A typical build process would look something like this:

    .. code-block:: python

        with BuildContext(*args) as build_context:
            build_runner = BuildRunner(build_context)
            build_report: BuildReport = build_runner.build()
            build_report.save()

    """
    def __init__(self, build_context: BuildContext):
        self.context = build_context

        self.config = Config()
        self.test_runner = TestRunner()

    def build(self) -> BuildReport:
        """Actually performs the build process and returns a BuildReport object about the result.

        This build process involves the following individual steps:

        - The remote git repository is cloned to the local system and checked out to the desired branch/commit.
        - The actual bit file is extracted from this repo.
        - This bit file is being used to flash the new configuration to the fpga board.
        - Finally the desired test suite is being run with this new hardware version.

        :return: A BuildReport object which contains all the informations and metrics about the build process which are
        important for the user.
        """
        try:
            click.secho('| | BUILDING FROM SOURCE | |', bold=True)
            # -- CLONING THE REPO
            self.clone()

            # -- FLASHING THE BIT FILE
            self.copy_bitfile()
            self.flash()

            # -- RUNNING THE TEST SUITE
            self.test()

            # -- SETTING THE END TIME
            self.context.end_datetime = datetime.datetime.now()

        except Exception as e:
            click.secho('[!] Build Exception: {}'.format(str(e)), fg='red')
        finally:
            return BuildReport(self.context)

    def test(self):
        """Executes the test suite with the new hardware version

        :return: void
        """
        # -- RUN THE TESTS
        self.test_runner.load()
        click.secho('    Tests have been loaded from memory')

        test_report = self.test_runner.run_suite(self.context.test_suite)
        click.secho('    Executed test suite: {}'.format(self.context.test_suite))
        click.secho('(+) Test report saved to: {}'.format(self.test_runner.folder_path), fg='green')

        # -- STORE THE TEST REPORT
        # The test report later also needs to be referenced to produce the build report, so it needs to be saved as
        # part of the build context object as well. The context object already has the attribute 'test_report', which
        # was initialized to none in the constructor.
        self.context.test_report = test_report

    def flash(self):
        """Flashes the bit file to the fpga board.

        NOTE: For this method to work properly, the attribute 'bitfile_path' of the context object has to be set
        correctly already. This is not being done in this method

        :return: void
        """
        # For the flashing process there already exists an CLI command within this very application. So the simplest
        # thing is to just invoke this command to do the flashing process here.
        exit_code = execute_command('ufotest flash {}'.format(self.context.bitfile_path), True)
        if exit_code:
            # TODO: there seems to be a problem where the flash command does not reurn exit code 1 even with an error.
            click.secho('[!] There was a problem flashing the bitfile!', fg='red')
        click.secho('(+) New bitfile flashed to the hardware', fg='green')

    def copy_bitfile(self):
        """Copies the bitfile from the cloned repo to the build folder for this build.

        The responsibility of this function is to find the bit file (this is the file which can be used to actually
        flash the new configuration onto the hardware) within the cloned repo folder. This bitfile then has to be
        copied from the repo to the build folder so it is stored for later reference. Also the path to this bit file
        has to be stored as an attribute of the context object.

        :return: void
        """
        # -- FIND THE BITFILE
        # So before we can copy the bitfile we actually have to know where is is within the repo folder. This is not
        # such a trivial task. It would kind of be desirable if it were possible to discover it automatically in the
        # future. The way it currently works is that the relative path to this bit file has to be given in the ufotest
        # config file and this relative path will always be used to *hopefully* point at the correct bitfile.
        relative_path = self.config.get_ci_bitfile_path()
        bitfile_path = os.path.join(self.context.repository_path, relative_path)
        bitfile_name = os.path.basename(bitfile_path)

        # -- COPY IT INTO THE FOLDER
        bitfile_destination_path = os.path.join(self.context.folder_path, bitfile_name)
        shutil.copy(bitfile_path, bitfile_destination_path)

        # -- SET CONTEXT ATTRIBUTE
        # The context object actually already has the attribute 'bitfile_path'. It has been initialized as None within
        # the constructor.
        self.context.bitfile_path = bitfile_destination_path

    def clone(self):
        """Clones the remote git repository to the local machine and checking out the desired commit.

        :return: void
        """
        # TODO: Maybe raise some exceptions in this method.
        click.secho('    Cloning git repository: {}'.format(self.context.repository_url))

        # -- CLONING THE REPO
        clone_command = 'git clone --single-branch --branch "{}" "{}"'.format(
            self.context.branch,
            self.context.repository_url
        )
        exit_code = execute_command(clone_command, False, cwd=UFOTEST_PATH)
        click.secho('(+) Cloned git repo: {}'.format(self.context.repository_path), fg='green')

        # -- CHECKOUT CORRECT COMMIT
        checkout_command = 'git checkout "{}"'.format(self.context.commit)
        exit_code = execute_command(checkout_command, False, cwd=self.context.repository_path)
        click.secho('(+) Checking out commit: {}'.format(self.context.commit))

        # -- GET THE COMMIT NAME
        # Ok so here we are doing something weird... Quick explanation: The build process can be triggered without
        # an actual commit name. In that case, it will just use the most recent commit by specifying FETCH_HEAD. This
        # would actually be the commit name within the context object. And that works fine and stuff, but for the
        # report it would be nice if we had the actual commit name. This we can only actually get after we have
        # cloned the repo. So this command here gets the commit name and returns it. We then update the commit name
        # within the context object with this actual name, so that we can use this later in the report.
        hash_command = 'git rev-parse HEAD'
        commit_name = get_command_output(hash_command, cwd=self.context.repository_path).rstrip('\n')
        self.context.commit = commit_name


