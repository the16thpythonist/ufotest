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

0.3.2 (2020-08-?)
------------------

- Added installation packages for OpenSUSE to the documentation


TODO
----

- Add a method which checks for init and displays an error message of installation folder has not been initialized
- Add the installation of vivado.
    - Can we add the installer to the repository? If not download using curl
- Execute "setup_camera" and "teardown_camera" scripts before and after acquisition of a frame.
    - I could write a "Camera" context manager object...?
- Make a real help text for the init command
- Add the "init" command to the documentation.
