#!/bin/bash
# By Michele Caselle for UFO 6 / 20 MPixels - camera
# this script disables the LVDS lines threfore reduce teh Power dissipation
export PCILIB_MODEL=ipedma
export LD_LIBRARY_PATH=/usr/lib

echo "--------------------------------"
echo "-------  	Camera  -----------"
echo "------- Power UP   -------"
echo "--------------------------------"

pci -w 9000 DFFF
pci -r 9010 -s 1

sleep 0.2
pci -w 9000 E0FF
pci -r 9010 -s 1
sleep 0.2

pci -w 9000 e10F
pci -r 9010 -s 1
sleep 0.2

echo "DONE .. "  
