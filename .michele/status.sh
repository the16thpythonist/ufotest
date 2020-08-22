#!/bin/bash

# by Michele caselle for 20MPixel - camera
echo "-----------------------------"
echo "----  S T A T U S ---------"
echo "-----------------------------"

BAR=`pci -i | grep "BAR 0" | awk '{print $6}' | cut -c -6` # it was -4 for cut, uros

function rd() {
    #pci -r $BAR"00$1" -s 10
    pci -r $BAR"$1" -s 14 # uros
}
pci -r $BAR"9000" -s 120
value=`pci -r 0x9110 -s 8 | grep 9110 | awk '{print $2}' | cut -c 1-8`
sensor_tmp=${value:4:4}
fpga_tmp=${value:0:4}
fpga_mon=${value:0:1}


# val=6f00 ######################################################
# pci -w 0x9000 $val
#pci -r 0x9000 -s 10
sleep 0.01
# value=`pci -r 0x9000 -s 8 | grep 9010 | awk '{print $2}' | cut -c 4-8`
# if [ "$value" != "b$val" ]; then
    # echo "--------------------------------->>>> ERROR! read value: ${value:1:4}, written value: $val"
    # error=1
    # exit
# fi
# value=`pci -r 0x9040  | awk '{print $2}' | cut -c 1-1`
# if [ "${value:4:1}" == "0"  ]; then
# if [ $value -ge 8  ]; then
#     echo "40 MHz"
#     clk_mhz=40
#     clk_ratio=$(echo "scale = 2; 40/40" | bc)
# else
#     echo "48 MHz"
#     clk_mhz=48
#     clk_ratio=$(echo "scale = 2; 48/40" | bc)   
# fi

value=`pci -r 9030 | awk '{print $2}' | cut -c 6-6`
if [ "$value" == "0"  ]; then
    echo "40 MHz"
    clk_mhz=40
    clk_ratio=$(echo "scale = 2; 40/40" | bc)
else
    echo "48 MHz"
    clk_mhz=48
    clk_ratio=$(echo "scale = 2; 48/40" | bc)   
fi
####### for 48 MHz use 48/40, for 40 MHz use 40/40 for clk_ratio 
######  offset can differ per device
######  datasheet values
# clk_ratio=$(echo "scale = 2; 40/40" | bc)
offset_zero_celsius=$(echo "scale = 2; 1000*$clk_ratio " | bc)
tmp_slope_sensor=$(echo "scale = 2; 0.3/$clk_ratio" | bc)

##     fpga monitor
let "fpga_mon=16#$fpga_mon"
fpga_mon=$(echo "ibase=10;obase=2;$fpga_mon" | bc)
fpga_mon=$(printf "%04d\n" $fpga_mon)
monitor_val=${fpga_mon:0:3}

#####  fpga temperature
let "fpga_tmp=16#$fpga_tmp"
fpga_tmp=$(echo "ibase=10;obase=2;$fpga_tmp" | bc)
fpga_tmp=$(printf "%016d\n" $fpga_tmp)
let "fpga_adc=2#${fpga_tmp:3:10}"
fpga_tmp=$(echo "scale = 2; (($fpga_adc*503.975)/1024.)-273.15   " |bc)


#####   sensor temperature
let "sensor_tmp=16#$sensor_tmp"
#use 48/40 for 40MHz, or 40/40 for 40 MHz main clock
# sensor_tmp=$(echo "scale = 2; ($sensor_tmp-1000.*(40./40.))*(0.3*(40./40.))" | bc)
sensor_tmp=$(echo "scale = 2; ($sensor_tmp-$offset_zero_celsius)*$tmp_slope_sensor" | bc)


# echo "Sensor temperature,according to the datasheet: $sensor_tmp C"
echo "Sensor temperature, clock $clk_mhz MHz: $sensor_tmp C"
echo "FPGA temperature: $fpga_tmp C"
if [ "$monitor_val" != "000" ]; then
    echo "ERROR FPGA MONITOR: $monitor_val"
    # exit
else
    echo "MONITOR OK"
fi
