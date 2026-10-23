#!/bin/sh
D=D:/AI/Active/Metroid-Prime
( $D/.weaver/lv3.sh stop; sleep 4; $D/.weaver/lv3.sh start; sleep 2; $D/.weaver/lv3.sh newgame; $D/.weaver/rt3.sh run hangar_field1; echo BOOT3-DONE ) > $D/work/run_play3/boot3.out 2>&1
