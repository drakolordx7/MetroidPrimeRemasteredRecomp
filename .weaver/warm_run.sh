#!/bin/bash
# warm_run.sh TAG CAP [prof_run args]  -- S24: gameplay run of the warm exe, cold by default (no pipeline cache, no key file).
# env: EXE= another exe, SEED=1 starts from work/stutter_seed (warm keys + cache), SALT=text makes the driver compile every shader fresh
# (NXRT_NVN_SPIRV_SALT, unique text per cold run), PRESS= another button script, SECS= run length. Output: work/prof/TAG.* and a warm_report row.
cd /d/AI/Active/Metroid-Prime
export MSYS2_ARG_CONV_EXCL='*'
TAG=$1; CAP=$2; shift 2
EXE=${EXE:-D:/AI/Active/Metroid-Prime/game-build-warm/build/warm/mpr.exe}
RUN=work/run_prof_$TAG
rm -rf $RUN; mkdir -p $RUN
if [ "${SEED:-0}" = "1" ]; then cp work/stutter_seed/pipeline_cache.bin work/stutter_seed/pipeline_keys.bin $RUN/; fi
SALTARG=""; if [ -n "$SALT" ]; then SALTARG="--env NXRT_NVN_SPIRV_SALT=$SALT"; fi
python runtime/scripts/prof/prof_run.py --exe "$EXE" --cap $CAP --seconds ${SECS:-170} --tag $TAG --skip 20 --env NXRT_AUDIO_SINK=null --env NXRT_NVN_SHADER_CACHE=D:/AI/Active/Metroid-Prime/work/shader_cache/spirv $SALTARG --press "${PRESS:-A#1000,A#1800,A#2400,A#3000,A#3600,A#4200,A#4800,A#5400,A#6000}" "$@" > work/prof/$TAG.out 2>&1
python .weaver/lat_report.py work/prof/$TAG.trace --skip 20 --seconds 140 --json work/prof/$TAG.lat.json >> work/prof/$TAG.out 2>&1
python .weaver/st_summary.py $TAG > work/prof/$TAG.sum.txt 2>&1
python .weaver/warm_report.py $TAG --list 6 > work/prof/$TAG.warm.txt 2>&1
cat work/prof/$TAG.sum.txt work/prof/$TAG.warm.txt
