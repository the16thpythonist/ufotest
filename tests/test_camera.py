import unittest
from ufotest._testing import UfotestTestMixin

import numpy as np

from ufotest.camera import AbstractCamera, MockCamera, import_raw, InternalDictMixin


class TestInternalDictMixin(unittest.TestCase):

    def test_creating_subclass(self):
        """
        If a subclass can be created and an instance of this subclass can be instantiated without error
        """

        class Local(InternalDictMixin):

            default_values = {
                'time': 0
            }

            def __init__(self):
                InternalDictMixin.__init__(self)

        local = Local()
        self.assertIsInstance(local, Local)

    def test_creating_subclass_without_default_values_error(self):
        """
        The InternalDictMixin expects the subclass to define a static attribute "default_values". This method tests if
        the proper error is raised when this is missing.
        """
        with self.assertRaises(NotImplementedError):

            class Local(InternalDictMixin):
                pass

            local = Local()

    def test_normally_using_internal_dict(self):
        """
        If the normal functionality of the mixin can be used. This includes the three exposed methods supports_prop,
        set_prop and get_prop, which interact with the internal dict
        """
        class Local(InternalDictMixin):

            default_values = {
                'a': 0,
                'b': 0
            }

            def __init__(self):
                InternalDictMixin.__init__(self)

        # Now we are just going to try and use the get and set prop methods of this class
        local = Local()
        self.assertFalse(local.supports_prop('c'))
        self.assertTrue(local.supports_prop('a'))
        local.set_prop('a', 100)
        self.assertEqual(100, local.get_prop('a'))

    def test_overwrite_methods(self):
        """
        If providing an optional overwrite method works
        """
        class Local(InternalDictMixin):

            default_values = {
                'a': 0,
                'b': 0
            }

            def __init__(self):
                InternalDictMixin.__init__(self)

            def get_a(self):
                return 100

        local = Local()
        local.set_prop('a', 10)
        # In the class definition we provided an overwrite method for the "a" prop, which will always return 100, but
        # by setting 10 earlier, that value should still be in the internal dict.
        self.assertEqual(100, local.get_prop('a'))
        self.assertEqual(10, local.values['a'])




class TestMockCamera(UfotestTestMixin, unittest.TestCase):

    def test_construction_works(self):
        """
        Generally if a new instance can be created.
        """
        mock_camera = MockCamera(self.config)
        self.assertIsInstance(mock_camera, MockCamera)

    def test_set_up_and_tear_down(self):
        """
        If the camera behaves as expected in regards to it's state: Before the set up the camera should not be usable,
        only after. After tear down the camera should also not be usable anymore.
        """
        mock_camera = MockCamera(self.config)

        # On default the camera should not be usable without the set_up method having been called at least once
        self.assertFalse(mock_camera.poll())

        # After the set up, the camera should be usable (== poll returns true)
        mock_camera.set_up()
        self.assertTrue(mock_camera.poll())

        mock_camera.tear_down()
        self.assertFalse(mock_camera.poll())

    def test_get_frame(self):
        """
        If a frame can be retrieved from the camera object
        """
        mock_camera = MockCamera(self.config)
        mock_camera.set_up()

        frame = mock_camera.get_frame()
        self.assertIsInstance(frame, np.ndarray)
        self.assertNotEqual(0, frame[0, 0])
