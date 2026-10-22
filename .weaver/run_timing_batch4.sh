#!/bin/bash
# Final-config audio timing: build once, then runs under a compile load: two with the WAV capture, one without. .weaver/run_timing_batch4.sh
cd /d/AI/Active/Metroid-Prime
.weaver/boot_media.sh --seconds 12 > work/run_media/build_only.out 2>&1
for i in 1 2 3; do
  (.weaver/compile_load.sh > /dev/null 2>&1 &)
  sleep 10
  if [ $i = 3 ]; then export NOWAV=1; fi
  .weaver/audio_timing.sh t_final$i 0 0 75 > work/run_media/batch4_$i.out 2>&1
  grep "slow frame\|slow DSP" work/run_media/t_final$i.log | head -10 >> work/run_media/batch4_$i.out
  sleep 20
done
echo ALLDONE > work/run_media/batch4.done
