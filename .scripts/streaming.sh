#!/bin/bash
echo "--------------------------------------------------------------------"
echo "--------------------------- S T A R T  -----------------------------"
echo "--------------------- Streaming Acquisition ----------------------"
echo "--------------------------------------------------------------------"
rm streaming.out*

echo "Start the auto streaming for 1 second ..."

pci -w 9040 0x80000a01
BAR=`pci -i | grep "BAR 0" | awk '{print $6}' | cut -c -6` # it was -4 for cut, uros
pci -r $BAR"9000" -s 110 #uros
sleep 1
echo "Stop the auto streaming ... "
pci -w 9040 0x80000201
BAR=`pci -i | grep "BAR 0" | awk '{print $6}' | cut -c -6` # it was -4 for cut, uros
pci -r $BAR"9000" -s 110 #uros
usleep 1000

PCILIB_MODEL=ipedma pci -r dma0 -o streaming$1.out --multipacket --timeout 10000000
# usleep 400000


pci -r $BAR"9000" -s 110 #uros
usleep 1000

sleep 1
echo "Status ... "
pci -w 9040 0x80000201
usleep 10000
BAR=`pci -i | grep "BAR 0" | awk '{print $6}' | cut -c -6` # it was -4 for cut, uros
pci -r $BAR"9000" -s 110 #uros
echo "frame streaming$1.out "

ipedec -r 3840 --num-columns 5120 streaming$1.out -f
