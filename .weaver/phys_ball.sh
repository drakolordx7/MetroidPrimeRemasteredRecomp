#!/bin/sh
cd /d/AI/Active/Metroid-Prime
PY=tools/.venv/Scripts/python
for t in b1 b2; do
$PY tools/test/phys_table.py --exe D:/AI/Active/Metroid-Prime/game-build-play2/build/play2 --rates 60,120 --scenarios ball --tag $t --out D:/AI/Active/Metroid-Prime/work/run_play2/phys --jobs 1 > work/run_play2/phys_ball_$t.txt 2>&1
done
echo done > work/run_play2/phys_ball_done.txt
