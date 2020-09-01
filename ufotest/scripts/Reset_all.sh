#!/bin/bash
# By Michele Caselle for UFO 6 / 20 MPixels - camera
echo "--------------------------------"
echo "-------  	S T A R T  -----------"
echo "-- C O N F I G U R A T I O N  --"
echo "--------------------------------"

pci -w 9020 100
sleep 0.2
pci -w 9040 80000004
sleep 0.2
pci -w 9040 80000001
sleep 0.2

pci -w 9000 D483
pci -r 9010 -s 1

sleep 0.2
pci -w 9000 D603
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 D700
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 E107
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 DE48
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 E740
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 E866
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 E944
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 ECE4
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 EDD2
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 F45B
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 F55B
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 F92F
pci -r 9010 -s 1
sleep 0.2
pci -w 9000 FB66
pci -r 9010 -s 1

echo "Set the number of line to 3840 ... "  
pci -w 9000 9a00
sleep 0.2
pci -r 9010 -s1
sleep 0.2
pci -w 9000 9b0F
sleep 0.2
pci -r 9010 -s1

#echo "Set the start single of line to 255 ... "  
#pci -w 9000 98FF
pci -w 9000 9800
sleep 0.2
pci -r 9010 -s1
sleep 0.2
pci -w 9000 9900
sleep 0.2
pci -r 9010 -s1

echo "Set the exp time .. 4 ms"  
pci -w 9000 a0ff
sleep 0.2
pci -r 9010 -s1
sleep 0.2
pci -w 9000 a100
sleep 0.2
pci -r 9010 -s1
sleep 0.2

echo "Enable test pattern ... "	
pci -w 9000 d301
sleep 0.2
pci -r 9010 -s1

echo "FPGA Reset ... "	
pci -w 9040 80000005
sleep 0.2
pci -w 9040 80000201
sleep 0.2

echo "Set DMA timeout"
pci -w 64 ffffff
sleep 0.2

echo "Set the number of frame on CMOS internal frame generator"
pci -w 9000 9601
echo "Set 1 frame for each frame requested"
sleep 0.2

echo "finish .. "  
