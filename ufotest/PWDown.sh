#!/bin/bash
# By Michele Caselle for UFO 6 / 20 MPixels - camera
# this script disables the LVDS lines threfore reduce teh Power dissipation
export PCILIB_MODEL=ipedma
export LD_LIBRARY_PATH=/usr/lib

echo "--------------------------------"
echo "-------  	Camera  -----------"
echo "------- Power Down  -------"
echo "--------------------------------"

pci -w 9000 DF00
pci -r 9010 -s 1

sleep 0.2
pci -w 9000 E000
pci -r 9010 -s 1
sleep 0.2

pci -w 9000 e100
pci -r 9010 -s 1
sleep 0.2

echo "DONE .. "  
