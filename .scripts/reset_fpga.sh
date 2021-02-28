#!/bin/bash
# By Michele Caselle for POLARIS

export PCILIB_MODEL=ipedma

echo "---------- R E S E T ------------------"
pci -w 9040 0x5 
sleep 0.2

echo "---------- ENABLE R/W ------------------"
pci -w 9040 0x201 
pci -w 64 0ffffff

./IODELAY_Set.sh
