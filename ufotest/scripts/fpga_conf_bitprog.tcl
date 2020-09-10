open_hw
connect_hw_server
open_hw_target
refresh_hw_device [lindex [get_hw_devices xc7vx330t_0] 0]
set_property PROBES.FILE {} [get_hw_devices xc7vx330t_0]
set_property FULL_PROBES.FILE {} [get_hw_devices xc7vx330t_0]
set_property PROGRAM.FILE [lindex $argv 0] [get_hw_devices xc7vx330t_0]
program_hw_devices [get_hw_devices xc7vx330t_0]
refresh_hw_device [lindex [get_hw_devices xc7vx330t_0] 0]
