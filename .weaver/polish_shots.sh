#!/bin/bash
# one scripted run per prompt style, screenshots into work/polish_shots/<style>_N.png:
#   .weaver/polish_shots.sh "xbox playstation keyboard switch" [seconds] [first_shot_s] [bc7_cache dir]
# Runs the polish game build (game-build-polish, runtime-wt/polish) headless in work/run_polish, presses A at the given frames.
cd /d/AI/Active/Metroid-Prime
mkdir -p work/polish_shots work/run_polish
CACHE=${4:-D:/AI/Active/Metroid-Prime/work/run_polish/bc7_cache}
PRESS=${PRESS:-A#1000,A#1800,A#2400,A#3000,A#3600,A#4200,A#4800,A#5400,A#6000}
for st in ${1:-xbox}; do
  rm -f work/run_polish/shot_*.png
  tools/.venv/Scripts/python -I -c "
import re
p='work/run_polish/controls.ini'
try: s=open(p).read()
except OSError: s=''
if '[prompts]' in s: s=re.sub(r'(\[prompts\][^\[]*?style\s*=\s*)\w+', r'\g<1>$st', s, flags=re.S)
elif '[switch]' in s: s=s.replace('[switch]','[prompts]\nstyle = $st\n\n[switch]',1)
else: s+='\n[prompts]\nstyle = $st\n'
open(p,'w').write(s)"
  .weaver/boot_polish.sh --no-build --seconds ${2:-200} \
    --env NXRT_NVN_SHADER_CACHE=D:/AI/Active/Metroid-Prime/work/shader_cache/spirv \
    --env NXRT_NVN_BC7_CACHE=$CACHE \
    --env NXRT_PROMPTS_DIR=D:/AI/Active/Metroid-Prime/runtime-wt/polish/assets/prompts \
    --env "NXRT_BOOT_PRESS=$PRESS" --env NXRT_BOOT_SCREENSHOT_AT=${3:-50} --env NXRT_BOOT_SCREENSHOT_EVERY=${SHOT_EVERY:-10} > work/run_polish/last_$st.txt 2>&1
  for f in work/run_polish/shot_*.png; do cp "$f" "work/polish_shots/${st}_$(basename $f)"; done
  cp work/run_polish/mpr.log work/polish_shots/mpr_$st.log
done
