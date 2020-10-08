#!/bin/bash
echo "Set all IODEAL to Default.. "  

pci -w 9300 16
pci -w 9304 f
pci -w 9308 7
pci -w 930C 0
pci -w 9310 16
pci -w 9314 f
pci -w 9318 7
pci -w 931C 0
pci -w 9320 16
pci -w 9324 f
pci -w 9328 7
pci -w 932C 0
pci -w 9330 16
pci -w 9334 f
pci -w 9338 7
pci -w 933C 0

pci -w 9340 02
pci -w 9350 0000

sleep 0.2
pci -w 9040 80000002
sleep 0.2
pci -w 9040 80000001

echo "finish .. "  
