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
    cat impact_mem_batch_tmp.cmd | sed "s/FILENAME/$file/" > impact_mem_batch_script.cmd
    impact -batch impact_mem_batch_script.cmd
    echo "FLASH Memory is configured with mcs file: $file"
elif [ "$extension" == "bit" ]; then
    # if option -g is used the mcs file is generated
    if $fileGenFlag; then	
        cat impact_mem_file_gen_tmp.cmd | sed "s/FILENAME/$name/" > impact_mem_file_gen_script.cmd
        impact -batch impact_mem_file_gen_script.cmd
        echo ".mcs file generated"
        exit
    fi  
    cat impact_batch_tmp.cmd | sed "s/FILENAME/$file/" > impact_batch_script.cmd
    impact -batch impact_batch_script.cmd
    echo "FPGA is configured with bit file: $file"	
else
    echo "The file extension is not supported, please use .bit or .mcs files" >&2
    exit
fi

