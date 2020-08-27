#!/bin/bash

###################### by Michele Caselle and Uros Stafanovic ##################################################
############ Resent procedure and camera initialization for 10 -bit mode ######################################
pci --stop-dma dma1
sleep .1
pci --start-dma dma1
sleep .1
#check that all of the buffers are on the x1000 addresses
VAR=`cat /sys/class/fpga/fpga0/kbuf* | grep bus | cut -c 16- | grep -v 000`
i=0
while [ -n "$VAR" ]; do
    echo $VAR
    i=$(echo $i + 1 | bc)
    num=`cat /sys/class/fpga/fpga0/kbuf* | grep bus | cut -c 16- | grep -v 000 | grep -c [1-9]`
    echo "Buffer addresses not aligned; Redo:" $i " times," $num "buffers unaligned"
    pci --stop-dma dma1
    sleep .1
    pci --start-dma dma1
    sleep .05
    VAR=`cat /sys/class/fpga/fpga0/kbuf* | grep bus | cut -c 16- | grep -v 000`
    if [ "$i" -gt 10 ]; then
        echo "ERROR!!! Addresses still not aligned, stopping!"
        break
    fi
done
if [ -z "$VAR" ]; then
    echo "Buf addr aligned"
else
    echo "Buf addr UNALIGNED!!!"
fi


