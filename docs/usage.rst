=====
Usage
=====

The ufotest project provides a command line interface to install and test the UFO camera, which was developed at the
Institute of Data Processing (IPE) of the Karlsruhe Institute of Technology (KIT).

Overview
--------

The following is a small overview of the available commands:

- **init**: Initializes the necessary installation folder and a default configuration file, which is needed to use this
  command line interface
- **config**: Opens the config file for the ufotest project with the preferred editor
- **install**: Installs the necessary dependencies, which are required to operate the UFO camera
- **script**: Execute one of the bash scripts for the camera by name
- **setup**: Executes all the reset scripts, which are required to make the camera operational
- **frame**: Acquires a single frame from the camera and optionally displays it to the user
- **flash**: Flashes a new fpga configuration to the Hiflex board
- **test**: Runs either a single camera unittest or a suite of multiple unittests. A report file is generated and saved
  into the archive of competed test runs

Check CLI version
"""""""""""""""""

To check the version of `ufotest`, which is currently installed on your machine, run the "--version" option like this:

.. code-block:: console

    $ ufotest --version


Initializing the project
------------------------

The ufotest program needs to be installed into a folder. This folder has to be initialized first using the `init`
command. Executing this command will create a new folder on the machine, which will store all of the static assets
needed for ufotest. The default installation path is "$HOME/.ufotest":

.. code-block:: console

    $ ufotest init

Custom installation folder
""""""""""""""""""""""""""

You can change the installation path by setting a different path to the environmental variable `UFOTEST_PATH`. Note
however, that this variable also has to be set whenever any other command is being executed later on. So it would make
sense to add an according line to the local .bashrc file.

.. code-block:: console

    $ export UFOTEST_PATH=$HOME/custom/path
    $ echo "export UFOTEST_PATH=$HOME/custom/path" >> ~/.bashrc
    $ ufotest init

Configuring the project
-----------------------

The `ufotest` project relies on a series of parameters, which may change over time and/or have to be customized by the
specific users. Since there are too many parameters to implement them purely as command line options for the various
scripts, the project relies on a global configuration file. This configuration file will automatically be generated
from a default template whenever the `ufotest` package is being installed.

The config file will be installed into the following path "$HOME/.ufotest/config.toml". But an easier way to edit this
file is by using the built in `config` command:

.. code-block:: console

    $ ufotest config

This command will open the config file using the system's default editor.

Installing the project
----------------------

The first hurdle when initially setting up the UFO camera is the installation process for all of it's dependencies.
Among a series of required system packages, a lot of custom libraries only available from certain git repositories
are needed to get the camera going. These installation processes sometimes need specific build parameters and
environmental variables, which are not intuitively documented.

To ease this lengthy process, the `install` command aims to execute this automatically.

To simply install the project with all the default configurations into the current working directory, simply run the
following command:

.. code-block:: console

    $ ufotest install .

However it is likely that most of the default configuration will not match the actual setup. So in before installation,
run the `config` command and edit the following most important configuration details:

- **install.os**: Set this string according to your target operating system. Currently supported systems are "ubuntu"
  and "suse"
- **install.package_install**: Insert the linux base installation command for the package manager, which you are
  currently using. An example for the default ubuntu package installation would be "sudo apt-get -y install". Note that
  when using a non-default package manager for your distribution you will have to manually change the package names for
  all the dependencies.
- **camera.camera_width**/**camera.camera_height**: Set the integer dimension of the used camera sensor...

For further configuration options, please consult the comments within the config file.

Additional options
""""""""""""""""""

The `install` command offers some additional options which can be used to control the install behaviour.

- *verbose*: Show additional console output for all the sub commands, which are being executed (This includes for
  example the build process of all the custom libraries)
- *no-dependencies*: Skips the installation of the required custom libraries in case thay are eventually already
  installed
- *no-libuca*: Skips the installation of the libuca related libraries.


Executing Michele's scripts
---------------------------

Interaction with the camera is realized in the form of a few bash scripts. These scripts are also contained within the
`ufotest` project and can be executed using the `script` command.

Use the '--verbose/-v' option to show the echoed output of the script:

.. code-block:: console

    # Example for the status script
    $ ufotest script --verbose status

All available scripts can be listed using the `list-scripts` command.

.. code-block:: console

    $ ufotest list-scripts

This command will output a list of all registered scripts containing their identifier, by which they can be
invoked, the path of the actual file, a description and information about the author of the script.


Working with the camera
-----------------------

As of right now, the project also provides some basic functionality to interact with the camera.

Initializing the camera
"""""""""""""""""""""""

Before doing anything else, the camera has to be initialized. This can be done using the `setup` command. This command
executes the various reset scripts which are required to put the camera into it's default state (Use the
'--verbose' option to see the output of the individual scripts.)

.. code-block:: console

    $ ufotest setup --verbose

Acquiring a frame
"""""""""""""""""

After executing the `setup` command a new frame can be acquired, by executing the `frame` command.
This command will acquire a single frame from the camera and save it at the specified path. To actually open a new
window, which will display the image data use the '--display' option:

.. code-block:: console

    $ ufotest frame --output="/path/to/frame.raw" --verbose --display


Flashing a new FPGA configuration
---------------------------------

The FPGA board which interfaces the camera is a kind of programmable hardware, which means that it can also be
reprogrammed. These fpga "programs" come in the form of ".bit" files. The `flash` command uses these bit files to
reconfigure the fpga.

Prerequisites
"""""""""""""

It is important to note, that the fpga cannot just be programmed over the PCIe interface, with which it is usually
connected with the PC. To program the board an additional *programmer* (from Xilinx) is required. This programmer
connects with the fpga board using a JTAG connector and with the PC per USB cable.

Only if the following two conditions are met, the `flash` command will actually work:
1. The programmer must be turned on and correctly connected to the PC as well as the board.
2. The appropriate drivers for the programmer must be installed on the PC.

Flashing the board
""""""""""""""""""

If an appropriate ".bit" file exists, it can be used to program the fpga board like this:

.. code-block:: console

    $ ufotest flash --verbose /path/to/file.bit

.. note::

    It is important that the file actually has the file extension ".bit"


Running a camera test
---------------------

It is additionally possible to run camera tests. A camera test is a special test routine, which tests some features
related to the camera. This could for example be whether the acquisition of a frame works properly, but could also be
checking if some dependency is installed correctly.

Such a camera test is executed with the `test` command of the CLI. This command takes exactly one required argument:
The string identifier of the test. Each test has to be named with a unique identifier. For this example, we are going
to use the 'mock' test, which is only implemented for testing purposes.

.. code-block:: console

    $ ufotest test mock

This command will execute the 'mock' test. Every execution of a camera test creates a *test report*. Currently this test
report is only available as a markdown (report.MD) file. This report first of all contains meta informations about the
test run, such as the starting/ending time, the target operating system and the CLI version. Additionally, it contains
an overview and a detailed description of the test results of all the tests, which were included in the
test run.

By default, these test reports can be found in the path `$HOME\.ufotest\archive` (or `$UFOTEST_PATH/archive` for
custom install). Each test run will create a separate folder within this "archive". The folders will be named with the
date and starting time of their corresponding test runs. Within these folders the "report.md" can be found.

.. note::

    The naming convention for the folder names can be changed in the config file

Test suites
"""""""""""

By default the `test` command will execute only a single test by it's string name. Because that is not very useful,
there is also the possibility to run multiple tests in a sequence. For this purpose it is possible to define
*test suites*.

To run such a suite use the '-s/--suite' option for the `test` command and use the string name of the suite:

.. code-block:: console

    $ ufotest test --suite mock

Some existing test suites are the following:
- **full**: This contains all tests, which are implemented by default
- **mock**: Will only execute the "mock" test. For testing purposes

It is also possible to create a custom test suite. This can be done by adding an additional key value pair within the
"test/suite" section of the config file. The key will be the string name by which the suite will be identified and the
value is supposed to be a list of string test names. The tests will be executed in the order in which they appear in
this list.

.. note::

    To acquire the names of test to put into a custom suite, take a look at the "full" suite in the config file.
    It contains all tests, which are available.
