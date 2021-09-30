#!/bin/bash
# Version 2.0 April 29 2016
# Created by: Luis Ardila luis.ardila@bozica.co
# Simple script to configure FPGA or Flash memory using the batch mode of Impact

fileFlag=false
fileGenFlag=false

#Getting options from the commad line
while getopts ":f:g" opt; do
    case $opt in
    f) 	#f=file
        file=$OPTARG
        fileFlag=true
        extension=$(echo "${file#*.}")
        name=$(echo "${file%.*}")
        ;;
    g)  #g=generate memory file
        fileGenFlag=true
	;;
    \?)
        echo "Invalid option: -"$OPTARG"" >&2
        exit
        ;;
    :)
        echo "Option -"$OPTARG" requires an argument" >&2
        exit
        ;;
    esac
done

#Check for Vivadi installation
if [ -f "/opt/Xilinx/Vivado/2018.3/settings64.sh" ]; then
    source /opt/Xilinx/Vivado/2018.3/settings64.sh
fi


#Checking if vivado or vivado_lab command can be found
if [ -x "$(command -v vivado)" ]; then
  echo 'Found vivado' >&2
  load_sw=vivado
elif [ -x "$(command -v vivado_lab)" ]; then
  echo 'Found vivado_lab' >&2
  load_sw=vivado_lab
else
  echo 'Could not find vivado/vivado_lab! Exiting now...' >&2
  exit
fi

#Checking if option -f is used and if file exist
if ! $fileFlag; then
    echo "option -f must be included and the .bit or .mcs file name as argument" >&2
    exit
elif [ ! -f "$file" ]; then
    echo $file
    echo "File does not exist"
    exit
fi


if [ "$extension" == "mcs" ]; then
    $load_sw -nolog -nojournal -mode batch -source fpga_conf_mcsprog.tcl -tclargs $file
    echo "FLASH Memory is configured with mcs file: $file"
elif [ "$extension" == "bit" ]; then
    # if option -g is used the mcs file is generated
    if $fileGenFlag; then
        $load_sw -nolog -nojournal -mode batch -source fpga_conf_mcsgen.tcl -tclargs $file
        $load_sw -nolog -nojournal -mode batch -source fpga_conf_mcsprog.tcl -tclargs $file
        echo "$file.mcs file generated"
        echo "FLASH Memory is configured with mcs file: $file"
    else
        $load_sw -nolog -nojournal -mode batch -source fpga_conf_bitprog.tcl -tclargs $file
        echo "FPGA is configured with bit file: $file"
    fi
else
    echo "The file extension is not supported, please use .bit or .mcs files" >&2
    exit
fi
