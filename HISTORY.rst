=======
History
=======

0.1.0 (2020-08-13)
------------------

- First release on PyPI.

0.2.0 (2020-08-23)
------------------

- First actual release with content
    - "install" command to install ufotest command automatically
    - "config" command to edit global configuration file
    - "frame" command to acquire and display a single frame

0.3.0 (2020-08-24)
------------------

- Added additional package for SUSE which installs c++ compiler
- Fixed unhandled exception in "frame"
- Added additional output if a cmake installation fails
- fixed readme
- Added "init" command, which will setup the installation folder and the config file

0.3.1 (2020-08-25)
------------------

- Small adjustments to the documentation
- Added "status.sh" and "reset.sh" scripts from michele to the main code folder.

0.4.0 (2020-08-27)
------------------

- Added installation packages for OpenSUSE to the documentation
- Copied the power up and power down scripts from the IPE
- Copied the vivado start script from the IPE
- Now checking for a valid ufotest installation before every command, thus preventing running into an obvious exception.
- Added jinja2 to the requirements
- Added module "camera.py" instead of "capture.py" to contain all the camera related functionality
- Modified config file
    - Added "scripts" section, which allows the user to register custom commands.
- Added the "script" command: Executes (bash) scripts, which were registered in the project
- Added functions which setup and teardown the camera state
    - Execute them in "frame" command
- Added an option to "config" which allows to specify the editor

0.4.1 (2020-08-27)
------------------

- Fixed the MANIFEST.in file, which did not include the bash scripts in the distribution package

0.4.2 (2020-09-01)
------------------

- Removed the setup and teardown process from the "frame" command, because as of right now,
  the power up and down should not be called too often, because there are problems with the FPGA regarding that.
- registered 2 new scripts
    - pcie_init
    - reset_fpga
- Changed the parameter type for the output of the frame command from Path to File in the hopes of making it
  able to overwrite like this
- Fixed the image display using matplotlib

0.5.0 (2020-09-01)
------------------

- Moved the code to import a number N of raw images from a file to it's own function in camera.py
- Added commands:
    - setup: Will enable the camera to work
    - teardown: Will disable the camera to work. Be careful not to use this while the FPGA still has problems with
      power down
    - list-scripts: Displays a list of all scripts
- Registered scripts
    - reset_tp: Resets the fpag and enables the test pattern
    - reset_dma: Resets the DMA settings of the fpga
- Moved the scripts into their own folder
- Removed the installation of vivado. This is the responsibility of the user. Installation path can be given in the
  config file
- Added the necessary scripts for the flashing of the fpga
- changed "execute_script" so that changes folder to the script folder first

0.5.1 (2020-09-01)
------------------

- Enabled Sphinx autodoc
- The "frame" command now removes the prior frame buffer file before saving the new one
- Updated the "usage" section of the documentation

0.5.2 (2020-09-10)
------------------

- Added the file "VERSION" which will be used to set the current version of the project. This file will also be read
  used for the setup.py. The reasoning to create this is that it can also be used for a --version option for the CLI
- Added the option "--version" to the cli group

0.5.3 (2020-09-10)
------------------

- Fixed the inclusion of the VERSION file into the code package


0.6.0 (2020-09-10)
------------------

- Changed the config names "camera_height" and "camera_width" to "sensor_height" and "sensor_width"
- moved the "package_install" section within the config to the individual sections for the OS's. So now this does not
  have to be changed by the user, but instead is specific for the chosen operating system.
- Added the new "flash" command which can be used to flash a new .BIT file to the fpga
    - It uses the "vivado" command from an existing vivado installation to flash the bit file.
- extended the "usage" section of the documentation with the new flash command


0.7.0 (2020-09-18)
------------------

- Added the new "test" command, which will execute a camera test procedure
    - Added the "tests" subfolder within the package, which will hold files that define these kind of test routines.
    - Added the TestRunner class which will be used to execute all these tests
    - Added the AbstractTest class, which will act as the base class for defining new camera tests
    - Added the TestReport class, which will wrap the results of the execution of a TestRunner
    - Added the TestSuite class, which will represent a test suite consisting of multiple tests
- Added the "tests" section in the config file.
- Fixed the "camera_height" to "sensor_height" in the camera.py module
- Added the module "_testing.py", which provides utilities for unittesting of the project
    - Added the UfotestTestCase as a extension of the default unittest TestCase, which sets up the project installation
      folder within a temporary folder
- Tests
    - Fixed the errors within "test_ufotest"
    - Added "test_testing" which contains test cases for testing the TestRunner class


TODO
----

- Write a test function, which will take a frame and check it for some properties
    - In general I should think about how I want to deal with the tests in a broader conceptional context
      Maybe write some base classes etc?
- Auto detect the operating system?
- I could write a "Camera" context manager object...?
- Make "init" add the necessary stuff to the bashrc file. use jinja2?
- EEPROM Programmierung
- tcl Sprache
