#!/bin/bash
# By Michele Caselle for UFO 6 / 20 MPixels - camera

for i in $(seq 1 40); do echo $i && ./frame.sh; done
