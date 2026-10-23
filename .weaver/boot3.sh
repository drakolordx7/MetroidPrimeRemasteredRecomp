#!/bin/sh
# boot3.sh [steps...]: restart the play3 live game, New Game, then the given route steps (default: the three hangar steps). Logs to work/run_play3/boot3.out
D=D:/AI/Active/Metroid-Prime
( $D/.weaver/lv3.sh stop; sleep 4; $D/.weaver/lv3.sh start; sleep 2; $D/.weaver/lv3.sh newgame; $D/.weaver/rt3.sh run ${@:-hangar_field1 hangar_scan_panel hangar_field2}; echo BOOT3-DONE ) > $D/work/run_play3/boot3.out 2>&1
