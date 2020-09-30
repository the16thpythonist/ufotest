Camera Testing
==============

The previous section "usage" explained how the "test" command can be used to execute camera tests. The ufotest CLI
already comes with predefined tests. These can be viewed in the corresponding section of the config file.

But it is also possible to write custom camera tests. Custom camera tests are written using the Python programming
language. Custom tests are dynamically discovered every time the `test` command is being run. To add a custom test
simply put a python module into the folder `$HOME/.ufotest/tests`.

Of course, this module still needs the correct content. The following code example provides a boilerplate, which can be
extended, but which is usable the way it is.

.. code-block:: python

    """
    Module: mytest.py
    """
    from ufotest.testing import AbstractTest
    from ufotest.testing import MessageTestResult, AbstractTestResult

    # Every test is represented by a single class. (One module can contain multiple test
    # classes) This class has to be a child class of "AbstractTest"
    class MyTest(AbstractTest):

        # This is the name, by which the test will then be identified to run it with the
        # "test" command for example.
        # The name should be unique and not contain any whitespaces.
        name = "my_test"

        # This is the constructor of the class.
        # The code which is displayed here has to be copied.
        def __init__(self, test_runner):
            AbstractTest.__init__(self, test_runner)

            # YOUR CUSTOM SETUP CODE

         # The "run" method should contain all the code, which *actually* executes the test.
         # This method will be executed by the TestRunner.
         def run() -> AbstractTestResult:

            # YOUR TEST CODE

            # The "run" method has to return a child class of "AbstractTestResult".
            # MessageTestResult is a predefined child class. It is the simplest version,
            # which represents the result of the string by a single string. This string message
            # will then be inserted into the "detailed results" section of the test report.
            # The first argument is the integer exit code. This will define if the test was
            # successful (0) or not (1)
            return MessageTestResult(0, "My detailed message")

After having defined this module, it has to be placed into the "tests" folder. After that it can be used immediately:

.. code-block:: console

    $ ufotest test my_test


Next steps
""""""""""

Of course this barebones example is not really useful for write sophisticated tests. For this additional information
about how to interact with the camera are missing. This includes for example how to capture a frame, how to setup the
camera properly, how to send control commands etc...

You can visit the github page of this project and read some of the predefined tests within the folder
"ufotest/tests" to get some inspiration. For more detailed information about the functions and classes which are
provided by the "ufotest" package, visit the section "API Documentation" of this documentation.
