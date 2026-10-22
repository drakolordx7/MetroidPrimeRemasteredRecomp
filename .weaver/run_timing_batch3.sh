#!/bin/bash
# Three audio timing runs on the paced device under a realistic compile load (a clean rebuild of a runtime worktree in the background).
cd /d/AI/Active/Metroid-Prime
.weaver/boot_media.sh --seconds 12 > work/run_media/build_only.out 2>&1
for i in 1 2 3; do
  (.weaver/compile_load.sh > /dev/null 2>&1 &)
  sleep 10
  .weaver/audio_timing.sh t_load$i 0 0 75 > work/run_media/batch3_$i.out 2>&1
  grep "slow frame\|slow DSP" work/run_media/t_load$i.log | head -10 >> work/run_media/batch3_$i.out
  sleep 20
done
echo ALLDONE > work/run_media/batch3.done
