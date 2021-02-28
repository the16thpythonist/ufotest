#!/bin/bash

echo "--------------------------------------------------------------------"
echo "--------------------------- S T A R T  -----------------------------"
echo "--------------------- Multi FRAME Acquisition ----------------------"
echo "--------------------------------------------------------------------"

rm mult*.out* 
echo "Set the number of frame ..."
read frame

pci -w 0x9170 $frame
sleep 0.1

pci -w 9040 0x80000201
sleep 0.1
echo "Send mult frame request ... "
pci -w 9040 0x800002f1
sleep 1
PCILIB_MODEL=ipedma pci -r dma0 -o mult$1.out --multipacket

sleep 1

echo "Status ... "
pci -w 9040 0x80000201
sleep 0.1
BAR=`pci -i | grep "BAR 0" | awk '{print $6}' | cut -c -6` # it was -4 for cut, uros
pci -r $BAR"9000" -s 110 #uros
echo "frame mult$1.out "
ipedec -r 3840 --num-columns 5120 mult$1.out -f

echo "Status ... "
echo "--------------------------------------------------------------------"
pci -r 9050 -s 12
echo "--------------------------------------------------------------------"
