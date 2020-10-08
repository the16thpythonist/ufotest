#!/bin/bash
# By Michele Caselle for UFO 6 / 20 MPixels - camera, date: August 2020
	
echo "--------------------------------------------------------------------"
echo "--------------------------- S T A R T  -----------------------------"
echo "-------------------- C O N F I G U R A T I O N  --------------------"
echo "---------------------- ( UFO 6 - 20 MPixel ) -----------------------"
echo "--------------------------- Normal Mode ----------------------------"
echo "--------------------------------------------------------------------"

pci -w 9020 100
sleep 0.2
pci -w 9040 80000005
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

echo "Set the start single of line to 0 ... "  
#pci -w 9000 98FF
pci -w 9000 9800
sleep 0.2
pci -r 9010 -s1
sleep 0.2
pci -w 9000 9900
sleep 0.2
pci -r 9010 -s1

echo "Set the number of line to 3840 ... "  
pci -w 9000 9a00
sleep 0.2
pci -r 9010 -s1
sleep 0.2
pci -w 9000 9b0F
sleep 0.2
pci -r 9010 -s1

echo "Set the subsampling to 0 ... "  
#pci -w 9000 98FF
pci -w 9000 9C00
sleep 0.2
pci -r 9010 -s1
sleep 0.2
pci -w 9000 9D00
sleep 0.2
pci -r 9010 -s1
pci -w 9000 9E00
sleep 0.2
pci -r 9010 -s1
sleep 0.2
pci -w 9000 9F00
sleep 0.2
pci -r 9010 -s1

echo "Set the min. value of exp time ... 96 us"  
pci -w 9000 a001
sleep 0.2
pci -r 9010 -s1
sleep 0.2
pci -w 9000 a1a0
sleep 0.2
pci -r 9010 -s1
sleep 0.2

echo "Enable test pattern ... "	
pci -w 9000 d300
sleep 0.2
pci -r 9010 -s1

echo "FPGA Reset ... "	
./reset_fpga.sh 

echo "Set DMA timeout"
pci -w 64 ffffff
sleep 0.2

echo "Set the number of frame on CMOS internal frame generator"
pci -w 9000 9601
sleep 0.2
pci -r 9010 -s1

echo "--------------------------------------------------------------------"
echo "finish .. "
echo "--------------------------------------------------------------------"
echo "status ..."  
pci -r 9050 -s 8 
