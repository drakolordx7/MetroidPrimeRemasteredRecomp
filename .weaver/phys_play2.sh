#!/bin/sh
# S25: physics table with the stuck tracker fix: the stall rates first, then the full table. Output work/run_play2/phys*.txt
cd /d/AI/Active/Metroid-Prime
PY=tools/.venv/Scripts/python
$PY tools/test/phys_table.py --exe D:/AI/Active/Metroid-Prime/game-build-play2/build/play2 --rates 60,230,236,250,288 --scenarios jump --tag stall --out D:/AI/Active/Metroid-Prime/work/run_play2/phys --jobs 1 > work/run_play2/phys_stall.txt 2>&1
$PY tools/test/phys_table.py --exe D:/AI/Active/Metroid-Prime/game-build-play2/build/play2 --rates 60,120,144,240 --tag full --out D:/AI/Active/Metroid-Prime/work/run_play2/phys --jobs 1 > work/run_play2/phys_full.txt 2>&1
echo done > work/run_play2/phys_done.txt
