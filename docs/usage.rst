=====
Usage
=====

The ufotest project provides a command line interface to install and test the UFO camera, which was developed at the
Institute of Data Processing (IPE) of the Karlsruhe Institute of Technology (KIT).

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

- *--verbose*: Show additional console output for all the sub commands, which are being executed (This includes for
  example the build process of all the custom libraries)
- *--no-dependencies*: Skips the installation of the required custom libraries in case thay are eventually already
  installed
- *--no-libuca*: Skips the installation of the libuca related libraries.
