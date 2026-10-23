#!/bin/bash
# st_run.sh TAG CAP [prof_run args]  -- S21: gameplay run of the stutter exe from a warm pipeline cache (work/stutter_seed; SEED=0 for a cold start),
# then the latency report, the stall attribution and the one-row summary. EXE= picks another exe, PRESS= another button script.
cd /d/AI/Active/Metroid-Prime
export MSYS2_ARG_CONV_EXCL='*'
TAG=$1; CAP=$2; shift 2
EXE=${EXE:-D:/AI/Active/Metroid-Prime/game-build-stutter/build/stutter/mpr.exe}
RUN=work/run_prof_$TAG
echo "other mpr.exe at start: $(tasklist | grep -ci "mpr")" > work/prof/$TAG.load
rm -rf $RUN; mkdir -p $RUN
if [ "${SEED:-1}" = "1" ]; then cp work/stutter_seed/pipeline_cache.bin work/stutter_seed/pipeline_keys.bin $RUN/; fi
python runtime/scripts/prof/prof_run.py --exe "$EXE" --cap $CAP --seconds 170 --tag $TAG --skip 20 --env NXRT_NVN_SHADER_CACHE=D:/AI/Active/Metroid-Prime/work/shader_cache/spirv --press "${PRESS:-A#1000,A#1800,A#2400,A#3000,A#3600,A#4200,A#4800,A#5400,A#6000}" "$@" > work/prof/$TAG.out 2>&1
echo "at end: $(tasklist | grep -ci "mpr")" >> work/prof/$TAG.load
python .weaver/lat_report.py work/prof/$TAG.trace --skip 20 --seconds 140 --json work/prof/$TAG.lat.json >> work/prof/$TAG.out 2>&1
python .weaver/stall_attr.py work/prof/$TAG.trace --skip 20 --seconds 140 --top 10 > work/prof/$TAG.stall.txt 2>&1
python .weaver/st_summary.py $TAG > work/prof/$TAG.sum.txt 2>&1
