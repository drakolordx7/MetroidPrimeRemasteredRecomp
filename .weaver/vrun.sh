#!/bin/bash
# validation run of the nvn2 build: .weaver/vrun.sh [seconds] [extra boot args]; summary of validation messages in work/run_nvn2/vsummary.txt
SECS=${1:-110}; shift
cd /d/AI/Active/Metroid-Prime
.weaver/boot_nvn2.sh --seconds $SECS "$@" --env NXRT_GFX_VALIDATION=1 --env "NXRT_BOOT_PRESS=${PRESS:-A@12,A@22,A@30,A@38,A@46,A@54,A@62,A@70,A@80}" --env NXRT_BOOT_SCREENSHOT_AT=14 --env NXRT_BOOT_SCREENSHOT_EVERY=${SHOT_EVERY:-8} > work/run_nvn2/last.txt 2>&1
tools/.venv/Scripts/python .weaver/vsum.py work/run_nvn2/mpr.log > work/run_nvn2/vsummary.txt
cat work/run_nvn2/vsummary.txt
