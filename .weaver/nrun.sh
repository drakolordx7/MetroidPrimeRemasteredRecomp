#!/bin/bash
# no-build run of the nvn3 game build, scripted into the game: .weaver/nrun.sh <seconds> [extra boot args]   (env PRESS, SHOT_AT, SHOT_EVERY, TRACE ...)
SECS=${1:-170}; shift
cd /d/AI/Active/Metroid-Prime
PRESS=${PRESS:-A#1000,A#1800,A#2400,A#3000,A#3600,A#4200,A#4800,A#5400,A#6000}
.weaver/boot_nvn3.sh --no-build --env NXRT_NVN_SHADER_CACHE=D:/AI/Active/Metroid-Prime/work/shader_cache/spirv --seconds $SECS "$@" --env "NXRT_BOOT_PRESS=$PRESS" --env NXRT_BOOT_SCREENSHOT_AT=${SHOT_AT:-60} --env NXRT_BOOT_SCREENSHOT_EVERY=${SHOT_EVERY:-20} > work/run_nvn3/last.txt 2>&1
tail -5 work/run_nvn3/last.txt
