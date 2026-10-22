#!/bin/bash
# retry a traced title frame until the "PRESS A" text is lit: snaps of draws 40..142 must differ between draws. usage: trace_press_a.sh [tries]
cd /d/AI/Active/Metroid-Prime
for i in $(seq 1 ${1:-4}); do
  rm -f work/run_prompts/snap_* work/run_prompts/trace_*
  SN=$(seq -s, 40 142)
  .weaver/boot_prompts.sh --no-build --seconds 100 --env NXRT_NVN_TRACE_AFTER_FS=42bb01 --env NXRT_NVN_TRACE_MIN_SEC=$((40+i*3)) --env NXRT_NVN_TRACE_SNAP=$SN --env NXRT_NVN_TRACE_SNAP_SAMPLED=0 > work/run_prompts/last.txt 2>&1
  n=$(tools/.venv/Scripts/python -I -c "
from PIL import Image, ImageChops
import glob,re
fs=sorted(glob.glob('work/run_prompts/snap_d*_RGBA8_SRGB.png'), key=lambda x:int(re.search(r'snap_d(\d+)_',x).group(1)))
prev=None;n=0
for f in fs:
    im=Image.open(f).convert('RGB')
    if prev is not None and ImageChops.difference(im,prev).getbbox(): n+=1
    prev=im
print(n)")
  echo "try $i: changed snaps $n"
  [ "$n" -gt 3 ] && break
done
