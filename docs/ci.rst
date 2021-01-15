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

Lastly, the version control system will have to be configured to send the appropriate webhooks to this machine when
new versions of the software are pushed to the remote repository. This will also be explained in more detail further
down the page.


Setting up a public hostname with NoIP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

to be done.


Configuration
-------------

An additional requirement for executing the ci functions of ufotest correctly is to enter the appropriate config values
into the config file which is located at '$HOME/.ufotest/config.toml'. This config file contains the section 'ci' which
looks like this:

.. code-block:: toml

    # This section mangages all the configuration for the CI (continuous integration) functionality of the application.
    [ci]
        repository_url = 'https://github.com/the16thpythonist/ufo-mock.git'
        bitfile_path = 'camera.bit'
        branch = 'main'
        hostname = 'localhost'
        port = 2424
        test_suite = 'mock'
        gmail_address = 'ipe.ufotest@gmail.com'
        gmail_password = 'enter password'

This listing explains how to configure each of the individual fields:

- **repository_url**: This has to be the string of the repository, that is being used as the basis for the CI process.
  this repository has to contain the source code and more importantly the BIT file which can be flashed onto the
  camera. It is important, that this url directs to the ".git" file of the repository.
- **bitfile_path**: This string defines a relative path. The basis of this path is the root folder of the above
  source code repository. The purpose of this path is to define the location of the BIT file within the repository.
  The ufotest application will attempt to flash the bit file at this location within the repository to the fpga board.
- **branch**: This is supposed to be the string name of the branch to be monitored with the CI functionality. A new
  build process will only be triggered if a commit is pushed to this branch. In this context it is advised to not use
  the default branch to connect to the ufotest application. Too many build requests could overload the application.
  Instead it would be good to use a separate "ci" branch, where commits are only made with the purpose of testing the
  changes on a real setup.
- **hostname**: This is supposed to be the hostname/web address under which the host machine running the ufotest
  application is reachable within the internet. On default this is localhost. With this configuration the CI web
  server only works for the local machine. It is advised to acquire a public hostname like "ufotest.com", which directs
  to the host machine from anywhere. Note: This can also be an actual IP address.
- **port**: This is the integer port number for the port on which the CI server is supposed to listen for incoming
  http requests.
- **test_suite**: This is the string name of the test suite, which is supposed to be executed for every new build.
- **gmail_address**: The gmail address to be used to deliver the automatic email notifications about a finished build
  process.
- **gmail_password**: The password for the previously mentioned gmail account


Automatic email notifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ufotest application offers the feature to automatically send an email notification after an automatically started
build was terminated. These emails are only being generated when a build is automatically triggered by a github webhook.
An email is sent to the person which has pushed the changes and the owner of the repository. The mail informs, that
the build has finished and provides a link to the build report.

To use this functionality, ufotest automatically accesses a google mail account from which it then sends these emails.
To be able to properly use this functionality, the "gmail_address" and "gmail_password" have to be set accordingly as
the credentials to an already existing account.


The CI command group
--------------------

The continuous integration functionality of the ufotest application is wrapped by the *ci* command group.
This command group contains all the necessary commands which will be used for these functions.
A list of all available commands can be obtained like this:

.. code-block:: console

    $ ufotest ci --help


Triggering a new build process
------------------------------

The essential functionality of this ci process is the build process for a new version of the source code. This process
can be triggered manually by using the 'build' command:

.. code-block:: console

    $ ufotest ci build --help

This command expects one argument, which is the string identifier of the *test suite* to be executed on the new version
of the source:

.. code-block:: console

    $ ufotest ci build "mock"

This command will then proceed to clone the branch / repo which was defined in the config file of the project. It will
search for the .bit file within this repository folder and then flash it to the hardware using the 'flash' command of
ufotest. The specified test suite will then be run on the new version and then the test report is saved to the archive.


Running the CI server
---------------------

This build functionality can also be triggered automatically once a new commit was pushed to a target source code
repository.
For this purpose, the ufotest app provides the option to run a server which listens for the appropriate requests. The
server can be started with the 'serve' command

.. code-block:: console

    $ ufotest ci serve --help

This command expects no arguments, however it depends strongly on the fields "ci.hostname" and "ci.value" of the
config file. These two values define which hostname the server will run under and on which port the server will listen.

.. code-block:: console

    $ ufotest ci serve

With the previous example, the web server could be reached from within a browser by supplying the address
``http://localhost:2424/``, as the default configuration for the hostname is "localhost" and the default port for
the ufotest application is 2424.
The browser will display the home page of the web interface of the server. On this page there are
all necessary navigation links to both the build and test report archive.

Hostname and port
~~~~~~~~~~~~~~~~~

The default port 2424 was chosen, so that the application could be run on a host machine which is already running a
different server on the default HTTP port 80. The port 80 and any other port can of course also be used for this
application, the corresponding field of the config file simply has to be changed accordingly. Although it is important
that there is no other application already attached to that port!

Choosing the hostname "localhost" only makes sense when the web interface should only be viewed from the very machine
which also runs the server. In case the web interface is also supposed to be accessible from within the local network
or the internet, a different public hostname/ip address has to be set in the config. Supplying the
correct hostname is important, because internally the program uses this hostname to assemble absolute urls to use for
the several navigation link elements in the web interface!

Configuring Github webhooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, the server only implements the possibility to respond to Github webhooks. Specifically those webhooks which
are triggered by a 'push' event. By the github standard it is possible to register a certain url to receive a http POST
request whenever a new push is made for the subject repo. This url would have to be configured to look like this
``http://{hostname}:{port}/push/github/``. If a push request is sent to this route, a new build process like described above
will be triggered.

CI web interface
~~~~~~~~~~~~~~~~

The ci server also offers a web interface, which can be accessed via any browser. Visiting the URL
``http://{hostname}:{port}/`` will display the home page of the server. This header element of this home page contains
navigational links to the most important pages of the interface.

The URL ``http://{hostname}:{port}/archive/`` directs to the list view of all archived test reports. For each test
report, some basic information is listed there. This information included for example the name of the executed test
suite, the amount of test cases run and the start and end time of the process. Each individual test report can be
accessed by using the corresponding web link.

The URL ``http://{hostname}:{port}/archive/`` directs to the list view of all archived build reports. For each
triggered build, some basic information is listed. The items of this list view also act as web links to direct to the
detailed page of each individual build report.




