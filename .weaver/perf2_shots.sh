#!/bin/bash
# perf2_shots.sh -- picture check: same presented frames with the pool view import on and off, PNGs in work/shots_perf2/v<0|1>
cd /d/AI/Active/Metroid-Prime
export MSYS2_ARG_CONV_EXCL='*'
for v in 1 0; do
  python runtime/scripts/prof/prof_run.py --exe D:/AI/Active/Metroid-Prime/game-build/build/perf2/mpr.exe --cap 60 --seconds 125 --tag shot_v$v --skip 20 --no-report --press "A#1000,A#1800,A#2400,A#3000,A#3600,A#4200,A#4800,A#5400,A#6000" --env NXRT_NVN_SHADER_CACHE=D:/AI/Active/Metroid-Prime/work/shader_cache/spirv --env NXRT_NVN_SHOT_FRAMES=3000,4500,6000,7000 --env NXRT_NVN_SHOT_DIR=D:/AI/Active/Metroid-Prime/work/shots_perf2/v$v --env NXRT_NVN_POOL_VIEW=$v > work/prof/shot_v$v.out 2>&1
done
