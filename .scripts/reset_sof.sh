#!/bin/bash

echo "--------------------------------"
echo "-------  R E S E T   -----------"
echo "--------- F P G A  -------------"
echo "--------------------------------"
 

pci -w 9020 100
sleep 0.2
pci -w 9040 80000004
sleep 0.2
pci -w 9040 80000005
sleep 0.2
pci -w 9040 80000201
sleep 0.2
sleep 0.2

./status.sh
echo "finish .. "  
