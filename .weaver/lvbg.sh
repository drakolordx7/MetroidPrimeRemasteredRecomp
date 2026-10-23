#!/bin/sh
# S25: run a live-driver command in the background, wait up to 100 s for it and print its output (if still running, say so; read work/run_play2/bg.out later)
OUT=/d/AI/Active/Metroid-Prime/work/run_play2/bg.out
rm -f $OUT.done
( /d/AI/Active/Metroid-Prime/tools/.venv/Scripts/python /d/AI/Active/Metroid-Prime/.weaver/live.py "$@" > $OUT 2>&1; touch $OUT.done ) &
i=0
while [ ! -f $OUT.done ] && [ $i -lt ${WAITS:-95} ]; do sleep 1; i=$((i+1)); done
cat $OUT
[ -f $OUT.done ] || echo "(still running: tail work/run_play2/bg.out; wait with lvbg.sh wait)"
