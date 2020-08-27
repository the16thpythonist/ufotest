#!/bin/bash
echo "Set all IODEAL to Default.. "  

pci -w 9500 16
pci -w 9504 f
pci -w 9508 7
pci -w 950C 0
pci -w 9510 16
pci -w 9514 f
pci -w 9518 7
pci -w 951C 0
pci -w 9520 16
pci -w 9524 f
pci -w 9528 7
pci -w 952C 0
pci -w 9530 16
pci -w 9534 f
pci -w 9538 7
pci -w 953C 0

pci -w 9540 02

sleep 0.2
pci -w 9040 80000002
sleep 0.2
pci -w 9040 80000001

echo "finish .. "  
