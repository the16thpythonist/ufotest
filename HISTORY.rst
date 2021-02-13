=======
History
=======

0.1.0 (13.08.2020)
------------------

- First release on PyPI.

0.2.0 (23.08.2020)
------------------

- First actual release with content
    - "install" command to install ufotest command automatically
    - "config" command to edit global configuration file
    - "frame" command to acquire and display a single frame

0.3.0 (24.08.2020)
------------------

- Added additional package for SUSE which installs c++ compiler
- Fixed unhandled exception in "frame"
- Added additional output if a cmake installation fails
- fixed readme
- Added "init" command, which will setup the installation folder and the config file

0.3.1 (25.08.2020)
------------------

- Small adjustments to the documentation
- Added "status.sh" and "reset.sh" scripts from michele to the main code folder.

0.4.0 (27.08.2020)
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

0.4.1 (27.08.2020)
------------------

- Fixed the MANIFEST.in file, which did not include the bash scripts in the distribution package

0.4.2 (01.09.2020)
------------------

- Removed the setup and teardown process from the "frame" command, because as of right now,
  the power up and down should not be called too often, because there are problems with the FPGA regarding that.
- registered 2 new scripts
    - pcie_init
    - reset_fpga
- Changed the parameter type for the output of the frame command from Path to File in the hopes of making it
  able to overwrite like this
- Fixed the image display using matplotlib

0.5.0 (01.09.2020)
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

0.5.1 (01.09.2020)
------------------

- Enabled Sphinx autodoc
- The "frame" command now removes the prior frame buffer file before saving the new one
- Updated the "usage" section of the documentation

0.5.2 (10.09.2020)
------------------

- Added the file "VERSION" which will be used to set the current version of the project. This file will also be read
  used for the setup.py. The reasoning to create this is that it can also be used for a --version option for the CLI
- Added the option "--version" to the cli group

0.5.3 (10.09.2020)
------------------

- Fixed the inclusion of the VERSION file into the code package


0.6.0 (10.09.2020)
------------------

- Changed the config names "camera_height" and "camera_width" to "sensor_height" and "sensor_width"
- moved the "package_install" section within the config to the individual sections for the OS's. So now this does not
  have to be changed by the user, but instead is specific for the chosen operating system.
- Added the new "flash" command which can be used to flash a new .BIT file to the fpga
    - It uses the "vivado" command from an existing vivado installation to flash the bit file.
- extended the "usage" section of the documentation with the new flash command


0.7.0 (18.09.2020)
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
- Added a "--force" flag to the "init" command, which will delte the entire installation tree first and then reinstalls
  it


0.8.0 (23.09.2020)
------------------

- Fixes
    - Fixed a broken dict index in install command
    - Fixed wrong config in _testing.py
    - Fixed naming error in default.toml
- Documentation
    - Added a short description for the items in the table of contents
    - Added a stub for an additional section which will contain notes about the camera itself
    - Changed the recommended way of installation to "from source" because then you could also run
      the unittests, which is pretty important
- Added the "archive" folder to be created with the "init" command. This folder will contain the results of
  the execution of a test runner.
- Added the "Config" singleton class, which should be used for config access in the future...
- Added a "general" section in the config file, which will store the date time format configuration for now, but
  will be used in the future for all configuration, which is not bound to any particular topic.
- Added the class "AbstractRichOutput", which will serve as an interface for all classes (mainly related to the
  testing functionality) which are supposed to implement plaintext, markdown and latex conversions...+
- Using jinja2 for templating in the project now
- Added the "templates" folder to the project. This folder will contain jinja2 templates, which will be used to
  generate the output for the test reports etc.
- Implemented Markdown conversion for TestReport and TestMetadata. The markdown versions of the test reports are now
  saved in an archive
- Added pytest to the requirements.txt

0.8.1 (23.09.2020)
------------------

- Fixes
    - Changed the file mode of the templates
    - Fixed the way to acces the sensor dimensions in the install.py module
- Documentation
    - Added the installation of python tkinter as a requirement
    - Changed the installation instructions to not use sudo anymore, but instead to modify PATH
- Added a "debian" option as operating system in the config file


0.8.2 (30.09.2020)
------------------

- Fixes
    - "test" command had the execution of a suite and a single test switched around
    - fixed the "get_command_output" function which was not working
    - fixed a minor issue in the test report markdown template
- Added
    - The run method of a single "AbstractTest" is now wrapped int a try/except statement.
    - The class "AssertionTestResult", which can be used for tests to define assertion cases.
        - Unittests for this class
    - Test suite "full" which is meant to contain all the tests in the future
- Changes
    - The "no-dependencies" flag of the "install" command now only skips the system packages
- Documentation
    - Extended "usage" with how to use the "test" command
    - Added additional section "tests", which explains how to write a custom test class.

0.8.3 (30.09.2020)
------------------

Fixes

- Fixed the access to the config values of the camera dimensions in the function which acquires
  a frame.
- fixed the install command

Changes

- Updated the readme

0.9.0 (05.12.2020)
------------------

Additions

- Added the python package 'md-to-html' to the list of requirements. It will be needed to convert the markdown output
  of the reports into actual html pages which can be viewed.
- Implemented a utility function to convert a markdown file into an html file.
- Added the python library 'flask' to the requirements. This library will be used to start a simple web server which
  will be responsible for reacting to the github hooks when new changes have been made to the repository.
- Added the 'ci' section to the config file. It contains all information which is necessary for the ci functionality
  such as the remote source repository url, which is to be monitored, the branch which is to be cloned and the public
  hostname of the host machine.
- Added new command group 'ci' which will contain all the commands necessary for the continuous integraion
  functionality of the application.
  - Added the 'run' command. It will clone the repository which was defined in the config file, flash the new version
  of the bitfile from the repo to the hardware and then run a test suite with this new hardware configuration.
  this command also aves a copy of the bit file version which was used for the process in the archive.
  - Added the 'serve' command. It will start a minimal flask web server which listens to the post request generated by
  the remote repository whenever a new commit has been pushed.
- The flask server, which is used to respond to git webhooks also serves the static files from the archive, which means
  that no additional nginx server has to be installed.

Changes

- Changed the function which clones the git repos to also be able to clone specific branches
- Started to unify the style of the console output of all the commands
- Reworked the "init" command to use the new style of console output, include a 'verbose' option and it now catches the
  error correctly if the folder already exists and the force flag is not set.

Documentation

- Added documentation which explains how to setup an nginx server to be able to view the test reports remotely using
  a browser.
- Fixed the issues with the documentation not building
- Fixed the Logo not being displayed in the documentation version of the readme


0.9.1 (06.12.2020)
------------------

Additions

- Added a little bit of a convenience function to the ci web server: When visiting the root web site. It will display
  a little help text now to see that the server is indeed running.

Changes

- Changed the route for the ci server which accepts the source control web requests from '/push' to '/push/github'
  because this leaves open the possibility to implement the custom web hooks of other source control systems in the
  future.

Documentation

- Added Documentation for the ci functions of the ufotest app


0.10.0 (17.12.2020)
-------------------

Additions

- A module 'ufotest.ci.email' which implements the functionality of sending emails in response to ci actions, which
  inform the different contributors of the package about the outcome of automated build triggers.
- The flask server now also serves the static html files from the 'builds' report folder
- Added a new folder 'static' to the project, which will contain all the static assets needed for the flask CI web
  server. These assets are mainly CSS and JS files as well as images etc. With the 'init' command this folder is being
  copied to the installation folder of the application. This is also the place where the files are actually being
  served. This has the advantage, that the files could be modified by the users.

Changes

- Fixed the broken code blocks in the CI part of the documentation.
- Moved the 'get_repository_name' function from ufotest.install to ufotest.util. Seems more intuitive
- Added the abstract method 'to_html' to the abstract base class AbstractRichOutput. Since it is now the plan that all
  relevant generated reports etc would be able to be viewed remotely over a web server, it would make sense to also
  generate the necessary html for this in the specific classes.
- Renamed the 'ci run' command to 'ci build'. I am referring to the process as a 'build' in all the comments and the
  documentation, so it is more consitent to actually also call the command itself like this
- Completely reworked the process of how the ci build works.
    - The ufotest installation folder now has an additional folder called 'builds' which will act as an archive for the
      build process much like the 'archive' folder works for test run reports. Having both of these seperately now is
      more consistent, becauses not every test run has to be part of a build, but every build contains a test run.
      the build report now simply links to the test report.
    - The implementation for this new process is in the module ufotest.ci.build
- Updated readme with credits for flask web framework

Documentation

- Renamed all occurrances of the build process to use the new name 'build' instead of 'run'


0.11.0 (14.01.2021)
-------------------

Additions

- TestReport now also generates an html page, which means that an online version of the test report can also be
  delivered using the CI server.
- AbstractTest cases now also have a "description" property where the test can be described. This description is then
  rendered to the test report as well
- The test reports and the build reports now also save as JSON files. This is important for procedurally parsing the
  information about a report later on, as it is needed for example to generate a list of all the tests/reports...
- CI server now also has a home page


Changes

- Changed the name of the static asset "build_report.css" to just "report.css". The very same stylesheet is also being
  used for the test report page.
- Added the new properties "repository_url" and "documentation_url" under the "general" section of the config file.
  These values are needed to display them in the web pages of the CI server.
- Refactored the testing procedure: Deprecated the old implementations of TestRunner, TestReport and TestMetadata and
  replaced them with new implementations.
  Added the new class TestContext. The way the testing process is now implemented internally functions much the same
  way as the build system. A new context manager has to be created for each new test run. This context is then first
  passed to the test runner, which actually executes the tests and writes the results back to the context. This "filled"
  context can then be passed to the test report constructor for the reporting functionality.
- Removed the "email" option from the "test" command.
- The jinja templates for the CI web server now use template inheritance, which was used to add a default header to
  each web page, which can be used to navigate between the most important pages.

Documentation

- Changed the documentation for the new "serve" command


0.12.0 (14.01.2021)
-------------------

Additions

- Added a test result class which allows to add images as a result.
- Added a test result class which allows to add dicts as a result.
- Test case which simply requests a frame from the camera and adds the image to the test report.
- Test case which requests frame and calculates simple statistics for it.

Changes

- Reworked the "mock" test case to now return a combined test result of one test result object for each available
  test result class. The mock test case thus became a way of testing test results classes.
- Fixed an error with including the static css files within the HTML templates of the CI server.
- Fixed the combined test result not having an html conversion.
- Changed the "serve" command: Now it has not arguments anymore. Both the hostname and the port now have to be defined
  in the config file. I realized that the html files for the reports are being created in separate instances of the
  application, which are not the running server and thus do not know the hostname or the port. This has lead to
  errors in the creation of the absolute url links within the html templates.

Documentation

- Changed the documentation for the "serve" command again


1.0.0 (15.01.2021)
------------------

Additions

- Created a new system for handling the builds. previously any build which was triggered while another one was still
  running would be rejected. Now there is a build Queue. When a build is triggered, it is added to this queue, which
  is essentially just a json file with a list. Then there is a separate process started by the "serve" command which
  only checks this queue and executes the build requests saved within.

Changes

- Fixed: The stylesheet for the build report html template was not linked to correctly.
- Fixed: There was an issue where the program would crash if two build would be triggered at the same hour and minute
  of the day since they would attempt to create folders with the same name. Added the build commit and the second of
  to the folder name format to fix.
- Fixed the bug that a build would not save the test reports properly.
- Fixed the build report url within the report email.

Documentation

- Updated the section about continuous integration.

1.0.1 (13.02.2021)
------------

Changes

- Changed the date format in the HISTORY.rst file
- Changed the default port from 2424 to 8030


TODO
----

- Document camera properties "Notes"
- Auto detect the operating system?
- Make "init" add the necessary stuff to the bashrc file. use jinja2?

