#!/bin/bash
# S14 oracle batch: HDR off/on screenshots with validation, window run with HDR auto (format log), window run with Reflex on + validation. Output in work/shots_s14.
cd /d/AI/Active/Metroid-Prime; mkdir -p work/shots_s14
P="A@12,A@22,A@30,A@38,A@46,A@54,A@62,A@70,A@80"
run() { name=$1; shift; rm -f work/run_extras/shot_*; .weaver/boot_extras.sh --no-build --seconds 115 --env "NXRT_BOOT_PRESS=$P" --env NXRT_GFX_VALIDATION=1 --env NXRT_BOOT_SCREENSHOT_AT=104 "$@" > work/run_extras/last.txt 2>&1; cp work/run_extras/mpr.log work/shots_s14/$name.log; for f in work/run_extras/shot_0*; do cp "$f" work/shots_s14/$name.${f##*shot_0.}; done 2>/dev/null; cp work/run_extras/shot_0.png work/shots_s14/$name.png 2>/dev/null; }
run hdr_off --env NXRT_HDR_MODE=off
run hdr_on --env NXRT_HDR_MODE=on
sed -i -e 's/^width = .*/width = 1920/' -e 's/^height = .*/height = 1080/' -e 's/^render_scale = .*/render_scale = 100/' work/run_extras/controls.ini
run window_auto --env NXRT_BOOT_GFX=window
run window_reflex --env NXRT_BOOT_GFX=window --env NXRT_LATENCY_MODE=on --env NXRT_LATENCY_LOG_TIMINGS=1
echo done > work/shots_s14/oracles_done.txt
