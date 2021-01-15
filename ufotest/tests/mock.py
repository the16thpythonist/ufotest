import time

import numpy as np
from PIL import Image

from ufotest.util import random_string
from ufotest.testing import (AbstractTest,
                             TestRunner,
                             MessageTestResult,
                             ImageTestResult,
                             CombinedTestResult,
                             DictTestResult)


class MockTest(AbstractTest):

    name = "mock"

    description = (
        "This test case is simply a mock, which is used to test the ufotest software tools. The test case does "
        "absolutely nothing. It returns a CombinedTestResult, which consists of every possible type of test result "
        "there is. This has been done to test if all the test result classes work properly."
    )

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):
        exit_code = 0

        # -- MESSAGE RESULT
        message = 'Mock test case message'
        message_test_result = MessageTestResult(exit_code, message)

        # -- IMAGE RESULT
        array = np.random.randint(0, 65535, size=(480, 720)).astype(np.uint16)
        image = Image.fromarray(array)
        image_path = '{}/{}.png'.format(self.context.folder_path, random_string(10))
        image.save(image_path)
        image_test_result = ImageTestResult(exit_code, image_path, 'A random image.', self.context.folder_url)

        # -- DICT RESULT
        table = {
            'key1':         'value1',
            'key2':         'value2',
            'key3':         'value3'
        }
        dict_test_result = DictTestResult(exit_code, table)

        time.sleep(10)

        return CombinedTestResult(
            message_test_result,
            image_test_result,
            dict_test_result
        )
