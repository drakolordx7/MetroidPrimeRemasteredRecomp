#!/bin/bash
# Audio timing runs on the paced device: .weaver/audio_timing.sh <name> <paced_ppm> <stress cores> [seconds]
# Runs the game headless with the paced sink and a WAV capture (NOWAV=1: no capture); prints the sink summary line. Needs a built mpr.exe (boot_media.sh builds it).
name=$1; ppm=$2; cores=$3; secs=${4:-75}
cd /d/AI/Active/Metroid-Prime
if [ "$cores" != "0" ]; then tools/.venv/Scripts/python .weaver/stress.py $cores $((secs+8)) & fi
wav="--env NXRT_AUDIO_WAV_DUMP=D:/AI/Active/Metroid-Prime/work/run_media/$name.wav"; [ -n "$NOWAV" ] && wav=""
.weaver/boot_media.sh --no-build --seconds $secs --env NXRT_AUDIO_SINK=paced --env NXRT_AUDIO_PACED_PPM=$ppm $wav > work/run_media/$name.out 2>&1
cp work/run_media/mpr.log work/run_media/$name.log
grep -o "audio: sink paced.\{0,170\}" work/run_media/$name.log | head -1
grep "underrun" work/run_media/$name.log | head -5 | cut -c1-160
wait
