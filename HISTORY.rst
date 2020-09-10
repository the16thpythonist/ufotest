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


TODO
----

- Put the version stuff into its own function...
- I could write a "Camera" context manager object...?
- Update documentation
    - Add init command
    - (Add frame command)
    - Add script command
    - Add option to define scripts in the config section
- Make "init" add the necessary stuff to the bashrc file. use jinja2?
- Figure out how to flash a bit file to the controller programmatically

