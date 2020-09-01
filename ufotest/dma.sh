#!/bin/bash
# By Michele Caselle for KAPTURE-2
echo "--------------------------------"
echo "------  	R E S E T  	---"
echo "------		D M A   	---"
echo "--------------------------------"

export PCILIB_MODEL=ipedma

echo "---------- R E S E T ------------------"
#pci -w 9040 0x1 
#sleep 0.2

echo "---------- S T O P   D M A ------------------"
pci --stop-dma dma0r
sleep 0.2

echo "---------- S T A R T  D M A ------------------"
pci --start-dma dma0r
sleep 0.2

echo "---------- LIST OF DMA ENGINES------------------"
pci --list-dma-engines
sleep 0.2

echo "---------- LIST OF DMA BUFFER------------------"
pci --list-dma-buffers dma0r
sleep 0.2

echo "---------- S T A T U S ------------------"
pci -r 9000 -s 100

sleep 0.2
#echo "---------- ENABLE R/W ------------------"
#pci -w 9040 0x400 

#echo "---------- S T A T U S ------------------"
#pci -r 9000 -s 100

