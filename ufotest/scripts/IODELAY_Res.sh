#!/bin/bash
echo "all IODEAL to 0 .. "  

pci -w 9300 1f
pci -w 9304 1f
pci -w 9308 1f
pci -w 930C 1f
pci -w 9310 1f
pci -w 9314 1f
pci -w 9318 1f
pci -w 931C 1f
pci -w 9320 1f
pci -w 9324 1f
pci -w 9328 1f
pci -w 932C 1f
pci -w 9330 1f
pci -w 9334 1f
pci -w 9338 1f
pci -w 933C 1f

pci -w 9540 02

sleep 0.2
pci -w 9040 80000002
sleep 0.2
pci -w 9040 80000001

echo "finish .. "  
