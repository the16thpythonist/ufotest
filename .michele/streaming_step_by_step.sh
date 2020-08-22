#!/bin/bash

rm stream*.out* 
echo "Start streaming for 1 sec ..."

pci -w 9040 801
pci -r 9000 -s 100
sleep 1.2
echo "Stop streaming... "
pci -w 9040 1
pci -r 9000 -s 100
usleep 100000
# usleep 400000
echo "Enable DDR reading ... "
pci -w 9040 201
pci -r 9000 -s 100
usleep 1000
pci -r dma0 -o streaming$1.out --multipacket --timeout 1000000

sleep 1
echo "Status ... "
usleep 10000
BAR=`pci -i | grep "BAR 0" | awk '{print $6}' | cut -c -6` # it was -4 for cut, uros
pci -r $BAR"9000" -s 110 #uros
echo "frame streaming$1.out "
