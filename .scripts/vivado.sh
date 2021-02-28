#!/bin/bash

#Check if Vivado is installed where we expect it to be
if [ -f /opt/Xilinx/Vivado/2018.3/settings64.sh ]; then

   #KIT License Servers
   export LM_LICENSE_FILE=50000@ipeflex1.fzk.de:27840@ls.itiv.kit.edu
   export MGLS_LICENSE_FILE=50000@ipeflex1.fzk.de:27840@ls.itiv.kit.edu
   export XILINXD_LICENSE_FILE=50000@ipeflex1.fzk.de:27840@ls.itiv.kit.edu

   #Mandatory Xilinx magic
   source /opt/Xilinx/Vivado/2018.3/settings64.sh

   #Workarounds to get Vivado to work on non-Ubuntu Linux
   #libtinfo5 was copied to /usr/lib/libtinfo5 from Vivado installation folder
   export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/libtinfo5
   
   #Vivado NEEDS system to be completely in English or it will break in very
   #strange ways
   export LANG=en_US.utf8
   export LC_ALL=en_US.utf8
   export XTERM_LOCALE=en_US.utf8

   #Start Vivado
   vivado
else
   echo "Couldn't find Vivado installation in /opt/Xilinx/Vivado/2018.3"
fi
