"""
Unittests for the building functionality of ufotest.
"""
import os
import datetime
import shutil

from ufotest._testing import UfotestTestCase
from ufotest.config import get_path
from ufotest.exceptions import IncompleteBuildError
from ufotest.ci.build import BuildContext, BuildLock, BuildRunner, BuildReport, BuildQueue

# == UTILITY DEFINITIONS ==


BUILD_CONTEXT_KWARGS = {
    'repository_url': 'https://github.com/the16thpythonist/ufo-mock.git',
    'branch_name': 'master',
    'commit_name': 'FETCH_HEAD',
    'test_suite': 'mock'
}


class MockBuildRunner(BuildRunner):

    def build(self):
        # ~ CREATING THE BITFILE
        bitfile_name = os.path.basename(self.config.get_ci_bitfile_path())
        bitfile_path = os.path.join(self.context.folder_path, bitfile_name)
        with open(bitfile_path, mode='w+') as bitfile:
            bitfile.write('Something...')
        self.context.bitfile_path = bitfile_path

        # ~ RUNNING THE TEST SUITE
        self.test()

        # ~ SETTING THE END TIME
        self.context.end_datetime = datetime.datetime.now()

        self.context.completed = True


class UfotestBuildTestCase(UfotestTestCase):

    def tearDown(self) -> None:
        UfotestTestCase.tearDown(self)

        # After every test we need to make sure that the build lock is released again or it will have an effect on all
        # the test which come after.
        if BuildLock.is_locked():
            BuildLock.release()

        # Additionally we need to clear the entire test and build archive
        for root, folders, files in os.walk(get_path('archive')):
            for folder in folders:
                folder_path = os.path.join(root, folder)
                shutil.rmtree(folder_path)

        for root, folders, files in os.walk(get_path('builds')):
            for folder in folders:
                folder_path = os.path.join(root, folder)
                shutil.rmtree(folder_path)


# == UNITTEST CLASSES ==


class TestBuildLock(UfotestBuildTestCase):

    # -- TESTS --

    def test_lock_path_is_relative(self) -> None:
        """
        If the lock file is actually within the correct installation folder.
        """
        self.assertEqual(os.path.dirname(BuildLock.get_lock_path()), get_path())

    def test_second_acquire_fails(self) -> None:
        """
        If a second call to "acquire" fails with the correct exception
        """
        BuildLock.acquire()
        self.assertTrue(BuildLock.is_locked())

        with self.assertRaises(PermissionError):
            BuildLock.acquire()

    def test_lock_and_release(self) -> None:
        """
        If locking and then releasing the lock works properly
        """
        BuildLock.acquire()
        self.assertTrue(BuildLock.is_locked())

        BuildLock.release()
        self.assertFalse(BuildLock.is_locked())

    def test_release_when_not_actually_locked(self) -> None:
        """
        If attempting to release the lock when it is not actually locked raises the correct exception
        """
        # First we need to make sure that the lock is not actually locked!
        if os.path.exists(BuildLock.get_lock_path()):
            os.remove(BuildLock.get_lock_path())

        with self.assertRaises(FileNotFoundError):
            BuildLock.release()


class TestBuildContext(UfotestBuildTestCase):

    # -- TEST --

    def test_construction(self):
        with BuildContext(**BUILD_CONTEXT_KWARGS, config=self.config) as build_context:
            self.assertIsInstance(build_context, BuildContext)


class TestBuildRunner(UfotestBuildTestCase):

    # -- TESTS --

    def test_construction(self):
        """
        If the construction of a new object instance works properly
        """
        with BuildContext(**BUILD_CONTEXT_KWARGS, config=self.config) as build_context:
            build_runner = BuildRunner(build_context)
            self.assertIsInstance(build_runner, BuildRunner)

    def test_construction_mock_build_runner(self):
        """
        If the construction of a new mock test runner object works properly
        """
        with BuildContext(**BUILD_CONTEXT_KWARGS, config=self.config) as build_context:
            build_runner = MockBuildRunner(build_context)
            self.assertIsInstance(build_runner, BuildRunner)


class TestBuildReport(UfotestBuildTestCase):

    # -- TESTS --

    def test_construction_with_mock_runner(self):
        """
        If a new object instance can be properly constructed by using the mock build runner
        """
        self.assertIn('context', self.config.data.keys())

        with BuildContext(**BUILD_CONTEXT_KWARGS, config=self.config) as build_context:
            build_runner = MockBuildRunner(build_context)
            build_runner.build()

            build_report = BuildReport(build_context)
            self.assertIsInstance(build_report, BuildReport)

    def test_construction_without_running_build(self):
        """
        If the attempt to create a new build report from a build context without actually running a build process prior
        results in the appropriate errors.
        """
        with BuildContext(**BUILD_CONTEXT_KWARGS, config=self.config) as build_context:
            with self.assertRaises(IncompleteBuildError):
                BuildReport(build_context)
