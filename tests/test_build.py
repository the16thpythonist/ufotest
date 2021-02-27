"""
Unittests for the building functionality of ufotest.
"""
import os

from ufotest._testing import UfotestTestCase
from ufotest.config import get_path
from ufotest.ci.build import BuildContext, BuildLock

# == UTILITY DEFINITIONS ==


BUILD_CONTEXT_ARGS = {
    'repository_url': 'https://github.com/the16thpythonist/ufo-mock.git',
    'branch_name': 'master',
    'commit_name': 'FETCH_HEAD',
    'test_suite': 'mock'
}


class UfotestBuildTestCase(UfotestTestCase):

    def tearDown(self) -> None:
        UfotestTestCase.tearDown(self)
        # After every test we need to make sure that the build lock is released again or it will have an effect on all
        # the test which come after.
        if BuildLock.is_locked():
            BuildLock.release()


# == UNITTEST CLASSES ==


class TestBuildLock(UfotestBuildTestCase):

    # -- TEST CASES --

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

    # -- TEST CASES --

    def test_construction(self):
        with BuildContext(**BUILD_CONTEXT_ARGS, config=self.config) as build_context:
            self.assertIsInstance(build_context, BuildContext)
