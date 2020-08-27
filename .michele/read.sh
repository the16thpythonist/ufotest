#!/bin/bash
rm bench.out
echo "--------------------------------"
echo "------  READ  D A T A 	---"
echo "--------------------------------"
pci -r dma0 --multipacket -o bench.out

