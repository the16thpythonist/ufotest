#!/bin/bash
# By Michele Caselle for POLARIS & KAPTURE-2
#echo "--------------------------------"
echo "------  D U M M Y   D A T A 	---"
echo "------		START   	---"
#echo "--------------------------------"
rm counter.out
pci -w 9040 0x8000201 
sleep 0.2

echo "---------- STOP ------------------"
pci -w 9040 0x0000201 

echo "---------- S T A T U S ------------------"
pci -r 9000 -s 100
 
