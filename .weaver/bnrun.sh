#!/bin/bash
# build the nvn3 game build, then nrun.sh: .weaver/bnrun.sh <seconds> [boot args]   (env as nrun.sh)
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\nvn3' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build-nvn3\build\nvn3' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime
pwsh -NoProfile -File game-build-nvn3/scripts/build.ps1 > work/run_nvn3/build.txt 2>&1 || { echo BUILD FAILED; grep -n "error" work/run_nvn3/build.txt | head; exit 1; }
exec .weaver/nrun.sh "$@"
