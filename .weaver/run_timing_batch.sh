#!/bin/bash
cd /d/AI/Active/Metroid-Prime
.weaver/boot_media.sh --seconds 12 > work/run_media/build_only.out 2>&1
.weaver/audio_timing.sh t_plus1500_stress 1500 24 75 > work/run_media/batch_a.out 2>&1
.weaver/audio_timing.sh t_minus1500_stress -1500 24 75 > work/run_media/batch_b.out 2>&1
.weaver/audio_timing.sh t_zero_idle 0 0 70 > work/run_media/batch_c.out 2>&1
echo ALLDONE > work/run_media/batch.done
