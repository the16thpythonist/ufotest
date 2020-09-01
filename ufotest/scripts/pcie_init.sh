#! /bin/bash

device=`lspci -vv | grep -m 1 Xilinx | awk '{print $1}'`
if [ -z "$device" ]; then
  echo "Xilinx device doesn't exist, rescanning..."
  echo 1 > /sys/bus/pci/rescan
  exit
else
  echo "Xilinx is located at: " $device
fi
echo "remove devices"
# echo 1 > /sys/bus/pci/devices/0000\:01\:00.0/remove
# echo 1 > /sys/bus/pci/devices/0000\:04\:00.0/remove
echo  1 > /sys/bus/pci/devices/0000\:${device:0:2}\:${device:3:4}/remove
sleep 1
echo "rescan"
echo 1 > /sys/bus/pci/rescan
sleep 1
echo "remove driver"
rmmod pciDriver
sleep 1
echo "instantiate driver"
modprobe pciDriver
# insmod /home/lorenzo/pcie/pcitool/driver/pciDriver.ko
sleep 1
# for devices with different ID
echo "10ee 6028" > /sys/bus/pci/drivers/pciDriver/new_id
# echo "10ee 6024" > /sys/bus/pci/drivers/pciDriver/new_id
pci -i
sleep .1
pci -r 9000
echo "set bus master dma"
# dev=04:00.0
dev=$device
echo Enabling bus mastering on device $dev
setpci -s $dev 4.w=0x07

export LD_LIBRARY_PATH=/usr/lib
export PCILIB_MODEL=ipedma

./dma.sh
