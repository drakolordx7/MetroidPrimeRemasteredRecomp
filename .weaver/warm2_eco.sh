#!/bin/bash
# warm2_eco.sh N -- S24: N rounds of the libraries run with (F) and without (B) efficiency-mode compile threads, alternating, cold (new salt each run)
cd /d/AI/Active/Metroid-Prime
for r in $(seq 1 ${1:-3}); do
  bash .weaver/warm2_queue.sh "ec_B$r:1:ecB$r:0:NXRT_NVN_COMPILE_ECO=0" > /dev/null 2>&1
  bash .weaver/warm2_queue.sh "ec_F$r:1:ecF$r:0:NXRT_NVN_COMPILE_ECO=1" > /dev/null 2>&1
done
echo done > work/prof/ec_done.txt
