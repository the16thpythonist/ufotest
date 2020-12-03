Setting up a CI Station
=======================

The main purpose of the testing functionality is mainly intended to be used for some kind of continuous integration
environment. The testing functionality of the ufotest tool is only one part of the whole setup that goes into such an
environment. The following sections will go into some detail about how the ufotest tool can be used to realize such a
CI like setup for the ufo camera.

Viewing Test Reports
--------------------

One main function of the ufotest tool is the creation of test reports. Whenever a test suite is executed, a new test
report is being generated. This test report is mainly represented as a markdown file which is being saved into an
archive folder for future reviews. This archive folder is located at the path *$HOME/.ufotest/archive*. For every test
run a new folder is created within this archive. These individual folders are named using the date and time at which
the test run was started. Witihin these folders there will always be a *report.md* file which contains the results of
the test run.

But of course this way of presenting the reports is very limited. It relies on the fact that at some point, someone
manually goes to the CI machine and looks up these report files. So there exists another possibility of viewing these
reports as html files from a remote location. This requires some additional effort though. Specifically, this requires
the installation of a web server on the target machine to be able to deliver static content. Additionally the CI
machine should also be accessable using a public domain name to be able to access it from anywhere.

As for the webserver *nginx* would be recommended due to the ease of usage. Install the nginx server using the OS
package manager:

.. code-block:: console

    $ sudo apt-get install nginx

Then configure the config file of nginx at */etc/nginx/nginx.conf* to look like the following

.. code-block:: text

    server {

        listen 80;
        server_name localhost;
        charset utf-8;

        location /archive {
            alias $HOME/.ufotest/archive;
        }
    }

Then you need to restart the server deamon:

.. code-block:: console

    $ sudo service nginx restart

.. note::

    It would be very beneficial if the machine would have a public domain name. This could for example be achieved with
    with comparebly low effort by using a public IPv6 address and a dynamic dns provider such as NoIP. If this were the
    case, the nginx config would have to be adjusted with the chosen hostname.


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
----------

Of course this barebones example is not really useful for write sophisticated tests. For this additional information
about how to interact with the camera are missing. This includes for example how to capture a frame, how to setup the
camera properly, how to send control commands etc...

You can visit the github page of this project and read some of the predefined tests within the folder
"ufotest/tests" to get some inspiration. For more detailed information about the functions and classes which are
provided by the "ufotest" package, visit the section "API Documentation" of this documentation.
