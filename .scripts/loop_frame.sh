#!/bin/bash
# By Michele Caselle for UFO 6 / 20 MPixels - camera
echo "--------------------------------------------------------------------"
echo "--------------------------- S T A R T  -----------------------------"
echo "-------------------------- LOOP FRAMEs  ----------------------------"
echo "--------------------------------------------------------------------"

for i in $(seq 1 40); do echo $i && ./frame.sh; done

echo "Status ... "
echo "--------------------------------------------------------------------"
pci -r 9050 -s 12
echo "--------------------------------------------------------------------"
