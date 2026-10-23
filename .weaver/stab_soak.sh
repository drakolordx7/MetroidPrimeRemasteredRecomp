#!/bin/bash
# S20: repeat the chain of areas that hung in the first sweep with the stab exe, one run folder per repeat.
#   .weaver/stab_soak.sh TAG REPEATS [env assignments for the game, e.g. NXRT_DISPLAY_FPS_CAP=0] 
# Output: work/soak_TAG/rN (sweep.py out folder), summary lines on stdout (status per area and load seconds).
export MPR_ROOT=D:/AI/Active/Metroid-Prime
TAG=$1; N=${2:-3}; shift 2
export NXRT_NVN_SHADER_CACHE='D:\AI\Active\Metroid-Prime\work\shader_cache\spirv' MSYS2_ARG_CONV_EXCL='*'
for kv in "$@"; do export "$kv"; done
EXE=${EXE:-game-build-stab/build/stab/mpr.exe}
AREAS=${AREAS:-'^(magmoor_fiery_shores|magmoor_geothermal_core|magmoor_lake_tunnel|phendrana_chapel_of_the_elders|phendrana_chapel_tunnel|phendrana_canyon_entryway)$'}
cd /d/AI/Active/Metroid-Prime
for i in $(seq 1 $N); do
  OUT=work/soak_$TAG/r$i
  rm -rf "$OUT"
  tools/.venv/Scripts/python tools-wt/stab/test/sweep.py --exe $EXE --out "$OUT" --md "$OUT/SWEEP.md" --cache work/sweep_cache_stab/bc7 --areas "$AREAS" --jobs 1 --chunk 6 --no-confirm --area-stall 240 --boot-stall 300 > "work/soak_$TAG.r$i.log" 2>&1
  tools/.venv/Scripts/python - "$OUT" "$TAG" $i <<'PY'
import json,sys
out,tag,i=sys.argv[1:4]
d=json.load(open(out+'/results.json'))['areas']
print(tag, 'repeat', i, ' '.join(f"{k.split('_',1)[1]}={v['status']}/{v.get('load_s')}" for k,v in d.items()))
PY
done
