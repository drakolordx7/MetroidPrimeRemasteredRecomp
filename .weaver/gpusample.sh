#!/bin/bash
# gpusample.sh OUT -- samples GPU utilisation every 2 s until killed
while true; do nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits >> "$1"; sleep 2; done
