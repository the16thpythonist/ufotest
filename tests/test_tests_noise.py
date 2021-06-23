import unittest
import matplotlib.pyplot as plt

from ufotest.testing import TestContext, TestRunner
from ufotest._testing import UfotestTestMixin
from ufotest.camera import MockCamera
from ufotest.tests.noise import CalculateDarkPhotonTransferCurve


class TestCalculateDarkPhotonTransferCurve(UfotestTestMixin, unittest.TestCase):

    def setUp(self):
        self.config.pm.register_filter('camera_class', lambda v: MockCamera)

    def test_run(self):
        """
        If the test essentially works
        """
        with TestContext(config=self.config) as test_context:
            test_runner = TestRunner(test_context)
            test = CalculateDarkPhotonTransferCurve(test_runner)
            
