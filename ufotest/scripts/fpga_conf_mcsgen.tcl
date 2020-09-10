set mcsfilename "[file rootname [lindex $argv 0]].mcs"
write_cfgmem -format mcs -interface bpix16 -size 32 -loadbit "up 0 [lindex $argv 0]"  -file $mcsfilename -force
