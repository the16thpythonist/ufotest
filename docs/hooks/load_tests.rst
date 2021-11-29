``load_tests`` - Filter
----------------------------------------

------------

Keyword Arguments
~~~~~~~~~~~~~~~~~

value: dict
    A dictionary, whose string keys are the unique string names of the test cases and the values are the
    subclasses of :code:`AbstractTest` which implement the functionality.

test_runner: TestRunner
    The test runner object which executes all the tests

Description
~~~~~~~~~~~

This hook is called on the :code:`self.tests` dict structure of the main :code:`TestRunner` instance *after* all
the tests from the filesystem have been loaded.

This dict has to be returned again.

Example
~~~~~~~

This hook can for example be used to add test case implementations without the need to specify a separate test module.
This should only be used when there are very few simple test cases, in which case a separate test module would be
overkill.

.. code-block:: python

    from ufotest.hooks import Filter
    from ufotest.testing import AbstractTest, MessageTestResult

    class HelloWorldTest(AbstractTest):

        def run(self):
            return MessageTestResult(0, "hello world")


    @Filter("load_tests", 10)
    def load_tests(value, test_runner):
        value['hello_world'] = HelloWorldTest
        return value
