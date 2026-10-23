#!/bin/bash
# perf2_run.sh TAG CAP [extra prof_run args]  -- gameplay run of the perf2 build with the S18 probe, then the latency report
cd /d/AI/Active/Metroid-Prime
TAG=$1; CAP=$2; shift 2
EXE=${EXE:-D:/AI/Active/Metroid-Prime/game-build/build/perf2/mpr.exe}
python runtime/scripts/prof/prof_run.py --exe "$EXE" --cap $CAP --seconds 170 --tag $TAG --skip 20 --env NXRT_NVN_SHADER_CACHE=D:/AI/Active/Metroid-Prime/work/shader_cache/spirv --press "${PRESS:-A#1000,A#1800,A#2400,A#3000,A#3600,A#4200,A#4800,A#5400,A#6000}" "$@" > work/prof/$TAG.out 2>&1
python .weaver/lat_report.py work/prof/$TAG.trace --skip 70 --seconds 90 --json work/prof/$TAG.lat.json >> work/prof/$TAG.out 2>&1
