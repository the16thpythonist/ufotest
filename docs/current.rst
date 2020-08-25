==================
Current Test Setup
==================

Currently a UFO camera test setup is located in the DAQ lab room of the Institute of Data Processing (IPE).

Computer
""""""""

A dedicated machine is used for just this purpose. This machine has the following credentials:

user: **ufo** - password: **........**

user **root** - password: **........**

On the ufo account all the necessary dependencies are already installed the camera is usable.

Secure Shell Access
"""""""""""""""""""

The previously mentioned machine itself is not reachable from the outside, but a port forwarding has been setup to
allow remote access to the machine using the following command:

.. code-block:: console

    $ ssh -Y -p 2424 ufo@daq-lab.ipe.kit.edu

Hardware
""""""""

The camera is either the 2048x2048 pixel version or the ?x? version depending on the current tests.

The camera is connected to the HighFlex FPGA board which was developed at the IPE.

Additionally the machine has a permanent connection to a Xilinx programmer, which is connected to the HighFlex board
so it can be programmed at any time.
