#!/bin/bash

rm interl*.out* 
echo "Write number of line ... 255 ..."
pci -w 9080 3FF
echo "Write number of start line ... 0 ..."
pci -w 9084 0
echo "Write number of skip line ... 4 ..."
pci -w 9088 A

pci -r $BAR"9000" -s 110 #uros
usleep 10000
pci -w 9040 401
pci -r 9000 -s 100
usleep 100000
echo "Stop streaming... "
pci -w 9040 1
pci -r 9000 -s 100
usleep 1000
# usleep 400000
echo "Enable DDR reading ... "
pci -w 9040 201
pci -r 9000 -s 100
usleep 1000
pci -r dma0 -o interl$1.out --multipacket --timeout 1000000

sleep 1
echo "Status ... "
usleep 10000
BAR=`pci -i | grep "BAR 0" | awk '{print $6}' | cut -c -6` # it was -4 for cut, uros
pci -r $BAR"9000" -s 110 #uros
echo "frame interl$1.out "
streaming$1.out
ipedec -r 3840 --num-columns 5120 interl$1.out -f
