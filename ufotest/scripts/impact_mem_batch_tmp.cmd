setMode -bs
setMode -bs
setMode -bs
setMode -bs
setCable -port auto
Identify -inferir
identifyMPM 
attachflash -position 1 -bpi "28F00AG18F"
assignfiletoattachedflash -position 1 -file "FILENAME"
Program -p 1 -dataWidth 16 -rs1 NONE -rs0 NONE -bpionly -e -v -loadfpga
setMode -bs
exit
