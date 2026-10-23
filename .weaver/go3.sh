#!/bin/sh
# go3.sh : after boot3.sh is done, drive the Frigate: corridor door, air lock, then frigate.py run to the reactor core. Output: work/run_play3/go3.out
D=D:/AI/Active/Metroid-Prime
( while ! grep -q BOOT3-DONE $D/work/run_play3/boot3.out; do sleep 5; done
  $D/.weaver/rt3.sh run hangar_corridor_door hangar_to_airlock
  $D/.weaver/fg3.sh run frigate frigate_reactor_core frigate_air_lock\>frigate_deck_alpha_mech_shaft
  echo GO3-DONE ) > $D/work/run_play3/go3.out 2>&1
