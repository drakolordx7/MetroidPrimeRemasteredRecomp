#!/bin/bash
# run of the nvn2 build WITHOUT validation, scripted to the game world: .weaver/trun.sh <seconds> [extra boot.py args]
# presses are keyed to presented frames (A#n); set TRACE=<present number> to log and dump the frame (NXRT_NVN_TRACE_FRAME)
SECS=${1:-300}; shift
cd /d/AI/Active/Metroid-Prime
PRESS=${PRESS:-A#1000,A#1800,A#2600,A#3400,A#4200,A#5000,A#5800,A#6600,A#7400,A#8200,A#9000,A#9800,A#10600,A#11400}
.weaver/boot_nvn2.sh --seconds $SECS "$@" --env "NXRT_BOOT_PRESS=$PRESS" --env NXRT_BOOT_SCREENSHOT_AT=${SHOT_AT:-14} --env NXRT_BOOT_SCREENSHOT_EVERY=${SHOT_EVERY:-30} ${TRACE:+--env NXRT_NVN_TRACE_FRAME=$TRACE} > work/run_nvn2/last.txt 2>&1
tools/.venv/Scripts/python .weaver/vsum.py work/run_nvn2/mpr.log | head -12
