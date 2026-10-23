#!/bin/sh
# warp3.sh AREA : warp the play3 live game to the area (development aid) and print the status
D=D:/AI/Active/Metroid-Prime
LIVE_RUN=$D/work/run_play3 LIVE_EXE=$D/game-build-play3/build/play3 $D/tools/.venv/Scripts/python -c "
import sys; sys.path.insert(0,'$D/.weaver')
import live as L
L.send(['@warp %s %s' % ('${2:-frigate}', '$1'), '@sleep 3000', 'wait 120'], 300)
print(L.fmt(L.status()))"
