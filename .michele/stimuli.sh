#!/bin/bash

rm mult*.out* 
echo "Set the number of frame ..."
read frame

pci -w 0x9170 $frame
usleep 10000

pci -w 9040 0x80000201
usleep 10000
echo "Send mult frame request ... "
pci -w 9040 0x800002f1
usleep 1000
# usleep 400000

# usleep 400000

pci -r dma0 -o mult$1.out --multipacket

sleep 1
echo "Status ... "
pci -w 9040 0x80000201
usleep 10000
BAR=`pci -i | grep "BAR 0" | awk '{print $6}' | cut -c -6` # it was -4 for cut, uros
pci -r $BAR"9000" -s 110 #uros
echo "frame mult$1.out "
ipedec -r 3840 --num-columns 5120 mult$1.out -f
