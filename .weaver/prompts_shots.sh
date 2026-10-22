#!/bin/bash
# one run per prompt style, screenshots into work/prompts_shots/<style>_N.png: .weaver/prompts_shots.sh "xbox playstation keyboard" [seconds]
cd /d/AI/Active/Metroid-Prime
mkdir -p work/prompts_shots
for st in ${1:-xbox}; do
  rm -f work/run_prompts/shot_*.png
  tools/.venv/Scripts/python -I -c "
import re,sys
p='work/run_prompts/controls.ini'
s=open(p).read()
if '[prompts]' in s: s=re.sub(r'(\[prompts\][^\[]*?style\s*=\s*)\w+', r'\g<1>$st', s, flags=re.S)
else: s=s.replace('[switch]','[prompts]\nstyle = $st\n\n[switch]',1)
open(p,'w').write(s)"
  .weaver/boot_prompts.sh --no-build --seconds ${2:-80} --env "NXRT_BOOT_PRESS=A#1500" --env NXRT_PROMPTS_DIR=D:/AI/Active/Metroid-Prime/runtime-wt/prompts/assets/prompts --env NXRT_BOOT_SCREENSHOT_AT=${3:-40} --env NXRT_BOOT_SCREENSHOT_EVERY=8 > work/run_prompts/last_$st.txt 2>&1
  for f in work/run_prompts/shot_*.png; do cp "$f" "work/prompts_shots/${st}_$(basename $f)"; done
  cp work/run_prompts/mpr.log work/prompts_shots/mpr_$st.log
done
