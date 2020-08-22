#!/bin/bash
echo "all IODEAL to 0 .. "  

pci -w 9500 1f
pci -w 9504 1f
pci -w 9508 1f
pci -w 950C 1f
pci -w 9510 1f
pci -w 9514 1f
pci -w 9518 1f
pci -w 951C 1f
pci -w 9520 1f
pci -w 9524 1f
pci -w 9528 1f
pci -w 952C 1f
pci -w 9530 1f
pci -w 9534 1f
pci -w 9538 1f
pci -w 953C 1f

pci -w 9540 02

sleep 0.2
pci -w 9040 80000002
sleep 0.2
pci -w 9040 80000001

echo "finish .. "  
