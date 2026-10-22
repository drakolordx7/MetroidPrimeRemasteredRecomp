#!/bin/bash
cd /d/AI/Active/Metroid-Prime
.weaver/boot_media.sh --seconds 12 > work/run_media/build_only.out 2>&1
(.weaver/compile_load.sh > /dev/null 2>&1 &)
sleep 10
.weaver/audio_timing.sh t_compile2 0 0 75 > work/run_media/batch2_a.out 2>&1
grep "slow frame\|slow DSP" work/run_media/t_compile2.log | head -20 >> work/run_media/batch2_a.out
echo ALLDONE > work/run_media/batch2.done
