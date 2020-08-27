#!/bin/bash

# hexdump -e ' "0x%08.8_ax: " 4/8 " 0x%08x " "\n" ' $1 | less
hexdump -e ' "0x%08_ax: " 8/4 " 0x%08X " "\n" ' $1 | less


