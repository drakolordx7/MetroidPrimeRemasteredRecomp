#!/bin/bash
# warm2_uncapped.sh -- S24: frame rate with no cap, whole pipelines against pipeline libraries (cold, new salt each): are linked pipelines slower on the GPU?
cd /d/AI/Active/Metroid-Prime
for r in 1 2; do
  for c in 0 1; do
    SECS=110 SALT=unc$c$r EXTRA="NXRT_NVN_GPL=$c" bash .weaver/warm2_run.sh unc_$c$r 0 --size 1920x1080 > work/prof/unc_$c$r.console 2>&1
  done
done
echo done > work/prof/unc_done.txt
