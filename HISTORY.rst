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

- Removed the setup and teardown process from the "frame" command, because as of right now, the power up
and down should not be called too often, because there are problems with the FPGA regarding that.
- registered 2 new scripts
    - pcie_init
    - reset_fpga


TODO
----

- Add the installation of vivado.
    - Can we add the installer to the repository? If not download using curl
- I could write a "Camera" context manager object...?
- Make a real help text for the init command
- Update documentation
    - Add init command
    - (Add frame command)
    - Add script command
    - Add option to define scripts in the config section
- Setup Sphinx autodoc for this project
- Make "init" add the necessary stuff to the bashrc file. use jinja2?
- Figure out how to flash a bit file to the controller programmatically

