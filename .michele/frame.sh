#!/bin/bash
# By Michele Caselle for UFO 6 / 20 MPixels - camera
echo "-----------------------------"
echo "----  SINGLE FRAME  ---------"
echo "-----------------------------"
rm bench.out*
sleep 0.1


echo "Start ... "

sleep .013001 
echo "Send frame request ... "
pci -w 0x9040 0x80000201
pci -w 0x9040 0x80000209
sleep .2
pci -r 9070 -s 4
pci -w 0x9040 0x80000201

sleep .01

pci -r dma0 --multipacket -o bench.out 
sleep .1
pci -r 9050 -s 12
sleep .1
rd_flag=1
echo "End ... "

echo "decoding..."
sleep .1
#ipedec -r 3840 --num-columns 5120 bench.out -v
ipedec -r 1088 --num-columns 2048 bench.out -v
