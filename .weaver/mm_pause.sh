#!/bin/sh
# S28: boot the mouse build, start a New Game with the mouse (play, slot, Normal), wait for control, open the pause screen. Usage: mm_pause.sh [K=V ...]  (writes work/mm_pause.out)
cd /d/AI/Active/Metroid-Prime
sh .weaver/mm.sh stop >/dev/null 2>&1; sleep 2
sh .weaver/mm.sh boot "$@" > work/mm_pause.out 2>&1
sh .weaver/mm.sh move 156 424 30 >> work/mm_pause.out; sh .weaver/mm.sh click Mouse1 300 >> work/mm_pause.out
sh .weaver/mm.sh move 450 345 20 >> work/mm_pause.out; sh .weaver/mm.sh click Mouse1 300 >> work/mm_pause.out
sh .weaver/mm.sh move 150 486 20 >> work/mm_pause.out; sh .weaver/mm.sh click Mouse1 100 >> work/mm_pause.out
sh .weaver/lvm.sh send "@sleep 25000" "@mashuntil A every 300 until igt >= 1" "@area frigate_exterior_docking_hangar" "@run 20 soft" >> work/mm_pause.out 2>&1
sh .weaver/lvm.sh send "@run 95 soft" >> work/mm_pause.out 2>&1
sh .weaver/mm.sh send "key Escape for 4" "wait 200" >> work/mm_pause.out
echo PAUSED >> work/mm_pause.out
