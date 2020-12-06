Continuous Integration
======================

As of version 0.0.9, one of the features of the ufotest app also includes basic functions for a continuous integration
like operation of a camera tests station. The following section explains the basic scenario where this functionality
would be needed.


The idea
--------

The ufo camera is based on an fpga board. This fpga is ultimately programmed with some source code to realize a
hardware configuration which interfaces with the actual camera module and provides the functionality of taking frames
and sending them to the host computer etc. The objective is to continuously monitor the state of this source code using
a dedicated test station. This test station will be always running and will be connected to a physical version of both
an fpga module as well as a camera. The idea is, that this test station is being remotely notified whenever a new
version of the source code is being submitted to the version control server (assuming github for example). Upon
receiving this notification the test station would attempt to flash this new version of the software to the hardware and
then run a series of tests on the camera to verify that this new version did indeed NOT break some of the functions.
This would then generate a test report, which would notify the contributors of the project of the status of this
monitoring.


Requirements
------------

The most important requirement for the setup of such a test station would of course be the access to the according fpga
and camera module which are to be tested with. Contrary to a normal user, the test station would also need a
*programmer device* for the fpga module, which has to be connected at all times to be able to flash the new versions
of the software to the device:

TODO: Include a link to the actual programmer which is being used at the moment.

Another important requirement is for the host machine, which will act as this test station, to have a public *hostname*.
Ultimately, the machine will be acting as a server which accepts requests from the version control system whenever a
change in the source code occurs. As such a server, the machine has to be in scope for the version control system to
be able to send the requests to the correct host machine.

TODO: Include tutorial of how to set up a public hostname.

Lastly, the version control system will have to be configured to send the appropriate webhooks to this machine when
new versions of the software are pushed to the remote repository. This will also be explained in more detail further
down the page.


Configuration
-------------

An additional requirement for executing the ci functions of ufotest correctly is to enter the appropriate config values
into the config file which is located at '$HOME/.ufotest/config.toml'. This config file contains the section 'ci' which
looks like this. The comments explain which values have to be entered for all the variables.

.. code-block:: toml

    # This section mangages all the configuration for the CI (continuous integration) functionality of the application.
    [ci]
        # This value is supposed to contain the string url of the repository, which contains the source code for the camera.
        # Since the camera is based on an FPGA board this source code will most likely be the code which defines the
        # hardware configuration of this fpga board. Most importantly, this repo has to contain the BIT file which can
        # be used to flash the new configuration onto the hardware.
        repository_url = 'https://github.com/the16thpythonist/ufo-mock.git'
        # This value then represents the path to the bit file which is to be used to flash the hardware. This string should
        # contain the relative path of the bit file within the repo. The current folder for this relative path will be
        # assumed to be the most top level folder of the repo.
        bitfile_path = 'camera.bit'
        # This value has to contain the string name of the branch which will be used for the cloning of the repository
        branch = 'main'
        # This value is supposed to contain the public hostname of the machine on which the application is running on. This
        # is important for the server funtion of the app. It is possible to start a server which listens to icoming requests
        # which are created by the git repository whenever new changes are being commited.
        hostname = 'localhost'
        # This value contains the string identifier of the test suite which is supposed to be executed whenever the build
        # process is automatically triggered by a git webhook
        test_suite = 'mock'


The CI command group
--------------------

As mentioned previously, the ufotest app actually implements the necessary software to achieve the described
functionality. This is mainly based on the 'ci' command group of the CLI. This command group contains all the necessary
commands which will be used for these functions. A list of all available commands can be obtained like this:

.. code-block:: console

    $ ufotest ci --help


Triggering a new build process
------------------------------

The essential functionality of this ci process is the build process for a new version of the source code. This process
can be triggered manually by using the 'run' command:

.. code-block:: console
    $ ufotest ci run --help

This command expects one argument, which is the string identifier of the test *suite* to be executed on the new version
of the source:

.. code-block:: console
    $ ufotest ci run "mock"

This command will then proceed to clone the branch / repo which was defined in the config file of the project. It will
search for the .bit file within this repository folder and then flash it to the hardware using the 'flash' command of
ufotest. The specified test suite will then be run on the new version and then the test report is saved to the archive.


Running the CI server
---------------------

This build functionality however is really only useful if it can be triggered automatically for every new version.
For this purpose, the ufotest app provides the option to run a server which listens for the appropriate requests. The
server can be started with the 'serve' command

.. code-block:: console

    $ ufotest ci serve --help

This command expects one argument which is the port at which the server is meant to operate.

.. code-block:: console

    $ ufotest ci serve 2424

Configuring Github webhooks
"""""""""""""""""""""""""""

Currently, the server only implements the possibility to respond to Github webhooks. Specifically those webhooks which
are triggered by a 'push' event. By the github standard it is possible to register a certain url to receive a http POST
request whenever a new push is made for the subject repo. This url would have to be configured to look like this
``http://{yourhostname}/push/github/``. If a push request is sent to this route, a new build process like described above
will be triggered.

Serving archived test reports
"""""""""""""""""""""""""""""

The ci server has yet another function: It will also respond to GET requests for the static ressources withing the
archive of the ufotest app.

Each execution of a test suite will create a new test report. This test report is saved as a MD file within the archive
folder of the app '$HOME/.ufotest/archive'. The report is also saved as an HTML file within the same folder. These html
files can then be used to view the results of the test runs remotely. The ci server will return these static read-only
files under the route ``http://{yourhostname}/archive/{testfolder}/report.html``.




