import unittest
from ufotest._testing import UfotestTestMixin

import numpy as np

from ufotest.camera import AbstractCamera, MockCamera, import_raw


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

