.. highlight:: shell

============
Installation
============

Requirements
------------

The projects needs python tkinter as one of it's dependencies. This will not be installed with pip, but has to
be installed with the operating systems project manager instead.

.. code-block:: console
    # Ubuntu/Debian
    $ sudo apt-get -y install python3-tk
    # OpenSUSE
    $ zypper install -y python3-tk

Stable release (Recommended)
----------------------------

This is the preferred method to install ufotest, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

To install ufotest, run this command in your terminal:

.. code-block:: console

    $ pip3 install ufotest

The executable files for the actual command line interface will *most likely* not be installed into a valid PATH
location. Instead the executable will be installed to `$HOME/.local/bin`. So this path has to be added to the PATH
variable for the executable to be callable from the console:

.. code-block:: console

    $ export PATH=$PATH:$HOME/.local/bin

**NOTE**: This extension of the PATH variable will be lost after a restart of the host machine. It is advised to add
this line to the bashrc file:

.. code-block:: console

    $ echo 'export PATH=$PATH:/$HOME/.local/bin' >> $HOME/.bashrc

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/

From sources
------------

The sources for ufotest can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/the16thpythonist/ufotest

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ sudo python3 setup.py install

The executable files for the actual command line interface will *most likely* not be installed into a valid PATH
location. Instead the executable will be installed to `$HOME/.local/bin`. So this path has to be added to the PATH
variable for the executable to be callable from the console:

.. code-block:: console

    $ export PATH=$PATH:$HOME/.local/bin

**NOTE**: This extension of the PATH variable will be lost after a restart of the host machine. It is advised to add
this line to the bashrc file:

.. code-block:: console

    $ echo 'export PATH=$PATH:/$HOME/.local/bin' >> $HOME/.bashrc

.. _Github repo: https://github.com/the16thpythonist/ufotest

Running Unittest (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is recommended to run the unittests of the project, if there are any problems with the project. This should provide
some insight into which kind of problem has occurred.

To run the unittests first navigate to the folder of the repository and then type:

.. code-block:: console

    $ sudo pytest tests/

Adding the script to PATH
-------------------------




Installing dependencies manually
--------------------------------

One of the features of the `ufotest` package is, that it wraps the lengthy installation process for all the
dependencies of the project and installs everything automatically.

But for the purpose of completeness and to preserve the knowledge, the following section will provide a step by step
guide of how to install all the dependencies manually. Note however that the more stable solution would be to use
the `install` command, since some of the URL's and parameters here are subject to change and may not be updated in
this documentation.

NOTE: The installation instructions include the setting of multiple environmental variables, so make sure to re-set
them all when using a new terminal instance, set them globally or just do the whole process in a single terminal...

NOTE: The console code examples of the following sections will include the current working directories, which are
assumed at that specific time of the installation process. These paths will most likely NOT match your current setup
so please adjust the absolute part of the path to match the installation directory you have chosen.

1. Installing system packages
"""""""""""""""""""""""""""""

The first thing to do is to install a series of system packages, which are needed for the following steps. Since
package names and package manager programs differ between linux distributions, this section will contain information
for all the tested plaforms.

**Ubuntu**:

.. code-block:: console

    $ sudo apt-get update
    $ sudo apt-get upgrade
    $ sudo apt-get -y install git curl gcc swig cmake uuid-dev xfsprogs xfslibs-dev python2 python2-dev doxygen uthash-dev libxml2 libxml2-dev libglib2.0 libgtk+2.0-dev gobject-introspection

**OpenSUSE**:

.. code-block:: console

    $ sudo zypper in -y git curl gcc gcc-c++ swig cmake uuid-devel xfsprogs-devel python2 python2-devel doxygen uthash-devel libxml2 libxml2-devel glib2-devel gtk2-devel gobject-introspection-devel



2. Creating the install folder
""""""""""""""""""""""""""""""

Next create a folder, into which all of the dependencies are being installed:

.. code-block:: console

    $ mkdir ufotest
    $ export UFOTEST_PATH=/home/user/ufotest
    $ cd $UFOTEST_PATH
    $ ls

3. Install fastwriter
"""""""""""""""""""""

`fastwriter` is a dependency for the ufo camera and can be installed with CMAKE.

.. code-block:: console

    $ cd $UFOTEST_PATH
    $ git clone http://fuzzy.fzk.de/gogs/UFO-libuca/fastwriter.git
    $ cd fastwriter
    $ mkdir build; cd build
    $ make -DCMAKE_INSTALL_PREFIX=/usr ..
    $ sudo make install

4. Install pictool
""""""""""""""""""

`pcitool` is a dependency for the ufo camera and can be installed with CMAKE.

.. code-block:: console

    $ cd $UFOTEST_PATH
    $ git clone http://fuzzy.fzk.de/gogs/jonas.teufel/pcitool.git
    $ cd pcitool
    $ mkdir build; cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=/usr ..
    $ sudo make install

Additional to the base `pcitool` project, the necessary *driver* also has to be installed

.. code-block:: console

    $ cd $UFOTEST_PATH/pcitool/driver
    $ mkdir build; cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=/usr ..
    $ sudo make install

To then actually activate the driver you'll also need to run the following command:

.. code-block:: console

    $ sudo depmod -a

5. Install libufodecode
"""""""""""""""""""""""

`libufodecode` is a dependency for the ufo camera and can be installed with CMAKE.

For this installation there are two important details:

- The cloning process of the repository fetches a specific tag, which is not the current head of master. That is because
  at the time of writing there is a bug in the most recent commit, which has not been sorted out yet. The given tag is
  the last working release.
- The sensor width in pixels has to be passed as a parameter to the build process, so that the raw data can be decoded
  properly later on!

.. code-block:: console

    $ cd $UFOTEST_PATH
    $ git clone https://github.com/ufo-kit/libufodecode.git
    $ cd libufodecode
    $ git checkout 508435541810172d1e6d3d684e1e081096233d97
    $ mkdir build; cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=/usr -DIPECAMERA_WIDTH=2048 ..
    $ sudo make install

6. Install libuca
"""""""""""""""""

`libuca` is a dependency for the ufo camera and can be installed with CMAKE.

.. code-block:: console

    $ cd $UFOTEST_PATH
    $ git clone https://github.com/ufo-kit/libuca.git
    $ cd libuca
    $ mkdir build; cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=/usr ..
    $ sudo make install

Additionally to the base library, the plugin `uca-ufo` for the ufo camera specifically has to be installed as well. It
is important to pass the sensor width *and* height to the build process

.. code-block:: console

    $ cd $UFOTEST_PATH
    $ git clone https://github.com/ufo-kit/uca-ufo.git
    $ cd "uca-ufo"
    $ mkdir build; cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMOSIS_SENSOR_WIDTH=2048 -DCMOSIS_SENSOR_HEIGHT=2048 ..
    $ sudo make install

7. Install ipecamera
""""""""""""""""""""

`ipecamera` is a dependency for the ufo camera and can be installed with CMAKE.

.. code-block:: console

    $ cd $UFOTEST_PATH
    $ git clone https://github.com/ufo-kit/ipecamera.git
    $ cd "ipecamera"
    $ mkdir build; cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=/usr ..
    $ sudo make install
