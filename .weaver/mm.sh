#!/bin/sh
# S28 driver for the mouse build (run folder work/run_mouse): mm.sh boot [K=V...] | move X Y [frames] | down|up [btn] | click [btn] | wheel DY | send "line"... | shot NAME | logs [N] | stop
cd /d/AI/Active/Metroid-Prime
L="sh .weaver/lvm.sh"
cmd=$1; shift
case "$cmd" in
  boot) ARGS="--env NXRT_PROMPTS_DIR=D:/AI/Active/Metroid-Prime/runtime-wt/mouse/assets/prompts"; for e in "$@"; do ARGS="$ARGS --env $e"; done
        $L start --gfx window $ARGS; $L send "wait 1500" "press A for 6" "wait 700" | tail -1 | cut -c1-30 ;;
  move) $L send "keydown mpos $1 $2" "wait ${3:-30}" | tail -1 | cut -c1-14 ;;
  click) B=${1:-Mouse1}; $L send "key $B for 5" "wait ${2:-60}" | tail -1 | cut -c1-14 ;;
  down) $L send "keydown ${1:-Mouse1}" "wait 20" | tail -1 | cut -c1-14 ;;
  up) $L send "keyup ${1:-Mouse1}" "wait 20" | tail -1 | cut -c1-14 ;;
  wheel) if [ "$1" -gt 0 ]; then K=WheelUp; else K=WheelDown; fi; $L send "key $K for 2" "wait 40" | tail -1 | cut -c1-14 ;;
  send) $L send "$@" | tail -1 | cut -c1-14 ;;
  shot) $L shot "$1" | tail -1 | cut -c1-60 ;;
  logs) $L send "wait 120" > /dev/null; grep -a "menumouse" work/run_mouse/live/mpr.log | grep -v "status:" | tail -${1:-12} | cut -c1-260 ;;
  stop) $L stop | tail -1 | cut -c1-20 ;;
esac
