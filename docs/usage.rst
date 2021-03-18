=====
Usage
=====

The ufotest project provides a command line interface to install and test the UFO camera, which was developed at the
Institute of Data Processing (IPE) of the Karlsruhe Institute of Technology (KIT).

After installing the "ufotest" package with the pip package manager as described earlier, the :code:`ufotest` command
is available from within the terminal. The :code:`--help` flag can be used to display a list of possible sub commands:

.. code-block:: console

    $ ufotest --help

The help flag can also be used for every subcommand of the application to list a short explanation of the commands
functionality and provide a list of required arguments as well as possible optional parameters.

The :code:`--version` flag can be used to display which version of the package (and thus command line interface) is
currently active.

.. code-block:: console

    $ ufotest --version

Overview
~~~~~~~~

The following listing is a small overview of the available commands, which are explained in further detail in their
corresponding sections.

- :ref:`init<init>` : Initializes the necessary installation folder and a default configuration file, which is needed to
  use the command line application.
- :ref:`config<config>` : Opens the config file for the ufotest project with the preferred editor
- :ref:`install<install>`: Installs the necessary dependencies, which are required to operate the UFO camera
- :ref:`script<script>` : Execute one of the bash scripts for the camera by name
- :ref:`setup<setup>` : Executes all the reset scripts, which are required to make the camera operational
- :ref:`frame<frame>` : Acquires a single frame from the camera and optionally displays it to the user
- :ref:`flash<flash>` : Flashes a new fpga configuration to the Hiflex board
- :ref:`test<test>` : Runs either a single camera unittest or a suite of multiple unittests. A report file is generated and saved
  into the archive of competed test runs


.. _init:

Initializing the project
------------------------

**Important**. Aside from the installation of the "ufotest" package via pip, the application also needs an installation
folder to work properly. This folder can to be initialized first using the :code:`init`
command. Executing this command will create a new folder on the machine, which will store all of the static assets
needed for ufotest. The default installation path is :code:`$HOME/.ufotest`.

.. code-block:: console

    $ ufotest init

Updating the installation folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The installed ufotest package can be updated to a new version using pip:

.. code-block:: console

    pip3 install ufotest --upgrade

It is highly likely that after an update of the python package, the installation folder also needs to be updated with
the assets of this new version. Using the init command with the additional flag :code:`--update` will replace the
static assets within the installation folder with the new versions from the python package, without affecting any other
details of the installation folder.

.. code-block:: console

    ufotest init --update

Replacing the installation folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When attempting to execute the init command again when there already exists an active installation folder will result
in an error. In the case that you do want to delete the current installation folder with all of it's saved data and
configuration to replace it with a fresh install, use the additional :code:`--force` flag:

.. code-block::

    ufotest init --force

.. _config:

Configuring the project
-----------------------

The `ufotest` project relies on a series of parameters, which may change over time and/or have to be customized by the
specific users. Since there are too many parameters to implement them purely as command line options for the various
scripts, the project relies on a global configuration file. This configuration file will automatically be generated
from a default template whenever the ufotest package is being installed by using the "init" command.

The config file will be installed into the following path :code:`$HOME/.ufotest/config.toml`. It can also be directly
edited by using the :code:`config` command:

.. code-block:: console

    $ ufotest config

This command will open the config file using the system's default editor. A specific editor can be supplied by using
the optional :code:`-e` parameter:

.. code-block:: console

    $ ufotest config -e nano


.. _install:

Installing the project
----------------------

The first hurdle when initially setting up the UFO camera is the installation process for all of it's dependencies.
Among a series of required system packages, a lot of custom libraries only available from certain git repositories
are needed to get the camera going. These installation processes sometimes need specific build parameters and
environmental variables, which are not intuitively documented.

To ease this lengthy process, the :code:`install` command aims to execute all of this automatically.

To simply install the project with all the default configurations into the current working directory, simply run the
following command:

.. code-block:: console

    $ ufotest install .

However it is likely that most of the default configuration will not match the actual setup. So before installation,
run the :code:`config` command and edit the following most important configuration details:

- **install.os**: Set this string according to your target operating system. Currently supported systems are "*ubuntu*"
  and "*suse*"
- **install.package_install**: Insert the linux base installation command for the package manager, which you are
  currently using. An example for the default ubuntu package installation would be :code:`sudo apt-get -y install`.
  Please note that
  when using a non-default package manager for your distribution you will have to manually change the package names for
  all the dependencies.
- **camera.camera_width**/**camera.camera_height**: Set the integer dimension of the used camera sensor in pixels.

For further configuration options, please consult the comments within the config file.

.. _script:

Executing Michele's scripts
---------------------------

Interaction with the camera is realized in the form of a few bash scripts. These scripts are also contained within the
`ufotest` project and can be executed using the :code:`script` command.

Use the optional :code:`--verbose` flag to show the stdout output which is generated by the scripts:

.. code-block:: console

    # Example for the "status" script, which prints the current status of the camera
    $ ufotest script --verbose status

All available scripts can be listed using the :code:`list-scripts` command.

.. code-block:: console

    $ ufotest list-scripts

This command will output a list of all registered scripts containing their identifier, by which they can be
invoked, the path of the actual file, a description and information about the author of the script.

.. _setup:

Initializing the camera
-----------------------

Before doing anything else, the camera has to be initialized. This can be done using the :code:`setup` command.
This command executes a series of bash scripts which are required to put the camera into it's default state (Use the
'--verbose' option to see the output of the individual scripts.)

.. code-block:: console

    $ ufotest setup --verbose

.. _frame:

Acquiring a frame
-----------------

After executing the :code:`setup` command a new frame can be acquired, by executing the :code:`frame` command.
This command will acquire a single frame from the camera. The image will be saved in the RAW image format. The
:code:`--output` parameter can be used to control the path to which the image is supposed to be saved:

.. code-block:: console

    $ ufotest frame --output="/path/to/frame.raw"

It is also possible to display the image to the user immediately after it was decoded. This can be achieved by also
supplying the optional :code:`--display` flag to the command:

.. code-block:: console

    $ ufotest frame --verbose --display

.. _flash:

Flashing a new FPGA configuration
---------------------------------

The FPGA board, which interfaces the camera, is a kind of programmable hardware, which means that it can also be
reprogrammed. These fpga "programs" come in the form of ".bit" files. The :code:`flash` command uses these bit files to
reconfigure the fpga.

Prerequisites
"""""""""""""

It is important to note, that the fpga cannot just be programmed over the PCIe interface, with which it is usually
connected with the PC. To program the board an additional *programmer* device (from Xilinx) is required. This programmer
connects with the fpga board using a JTAG connector and with the PC per USB cable.

Only if the following two conditions are met, the :code:flash` command will actually work:
1. The programmer must be turned on and correctly connected to the PC as well as the board.
2. The appropriate drivers for the programmer must be installed on the PC.

Flashing the board
""""""""""""""""""

If an appropriate ".bit" file exists, it can be used to program the fpga board like this. The path of the bit file has
to be supplied to the :code:`flash` command as a positional argument

.. code-block:: console

    $ ufotest flash --verbose /path/to/file.bit

.. note::

    It is important that the file actually has the file extension ".bit"

.. _test:

Running a camera test
---------------------

It is additionally possible to run camera tests. A camera test is a special test routine, which tests some features
related to the camera. This could for example be whether the acquisition of a frame works properly, but could also be
checking if some dependency is installed correctly.

Such a camera test is executed with the :code:`test` command of the CLI. This command takes exactly one required
argument: The string identifier of the test. Each test has to be named with a unique identifier. For this example,
we are going to use the 'mock' test, which is only implemented for testing purposes. This test should terminate
successfully in any case, even if the camera is not connected to the PC at all.

.. code-block:: console

    $ ufotest test "mock"

This command will execute the 'mock' test. Every execution of a camera test creates a *test report*.
This report first of all contains meta information about the
test run, such as the starting/ending time, the target operating system and the CLI version. Additionally, it contains
an overview and a detailed description of the test results of all the tests, which were included in the
test run.

By default, these test reports can be found in the path :code:`$HOME\.ufotest\archive`.
Each test run will create a separate folder within this "archive". The folders will be named with the
date and starting time of their corresponding test runs. Within these folders the "report.md" can be found.

Test suites
"""""""""""

By default the :code:`test` command will execute only a single test by it's string name. Because that is not very
useful in itself,
there is also the possibility to run multiple tests in a sequence. For this purpose it is possible to define
*test suites*.

To run such a suite, the optional :code:`--suite` flag of the test command can be used. If this flag is supplied
the given string name is not interpreted as the name of a single test, but instead as the string identifier of a test
suite (which is a list of tests). Thus the following command executes the "mock" test *suite*.

.. code-block:: console

    $ ufotest test --suite "mock"

It is also possible to create a custom test suite. This can be done by adding an additional key value pair within the
:code:`test.suite` section of the config file. The key will be the string name by which the suite will be identified
and the
value is supposed to be a list of string test names. The tests will be executed in the order in which they appear in
this list.

.. note::

    To acquire the names of test to put into a custom suite, take a look at the "full" suite in the config file.
    It contains all tests, which are available.
