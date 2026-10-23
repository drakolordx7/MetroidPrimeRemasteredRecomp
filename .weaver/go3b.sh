#!/bin/sh
# go3b.sh : after boot3.sh, bring the player to the air lock (no scans), then stop. Output: work/run_play3/go3b.out
D=D:/AI/Active/Metroid-Prime
( while ! grep -q BOOT3-DONE $D/work/run_play3/boot3.out; do sleep 5; done
  NOSCAN=1 $D/.weaver/rt3.sh run hangar_corridor_door hangar_to_airlock
  echo GO3B-DONE ) > $D/work/run_play3/go3b.out 2>&1
