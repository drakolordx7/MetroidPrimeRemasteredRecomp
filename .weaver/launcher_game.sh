#!/bin/bash
# S27: start the game through the launcher (--auto-play) in the test game folder and wait for that process (found by its command line) to end.
#   .weaver/launcher_game.sh <max seconds> [extra mpr.exe args]   env (NXRT_PLAY_SELFTEST, NXRT_NVN_SHOT_FRAMES ...) is passed on
ROOT=/d/AI/Active/Metroid-Prime
GAME=${GAMEDIR:-D:/AI/Active/Metroid-Prime/work/run_launcher/gamedir}
MAX=${1:-300}; shift
export NXRT_NVN_SHADER_CACHE='D:/AI/Active/Metroid-Prime/work/shader_cache/spirv'
"$ROOT/work/run_launcher/rel/mpr_launcher.exe" --game "$GAME" --auto-play --game-args "--log $GAME/launcher_run.log $*"
sleep 3
pid=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='mpr.exe'\" | Where-Object { \$_.CommandLine -like '*run_launcher*' } | Select-Object -First 1).ProcessId")
echo "game pid: $pid"
[ -z "$pid" ] && exit 1
t=0
while [ $t -lt $MAX ] && powershell -NoProfile -Command "if (Get-Process -Id $pid -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"; do sleep 5; t=$((t+5)); done
if powershell -NoProfile -Command "if (Get-Process -Id $pid -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"; then echo "still running after $MAX s: stopping pid $pid (started by this script)"; powershell -NoProfile -Command "Stop-Process -Id $pid -Force"; fi
echo "done after ~$t s"
