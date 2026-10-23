#!/bin/bash
# build mpr.exe from the nvn4 runtime worktree into game-build-nvn4/build/nvn4 (private copy of game-build); prints errors only
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\nvn4' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build-nvn4\build\nvn4' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime
mkdir -p work/run_nvn4
pwsh -NoProfile -File game-build-nvn4/scripts/build.ps1 -Runtime "$MPR_RUNTIME" -Out "$MPR_BUILD_DIR" > work/run_nvn4/build.txt 2>&1
rc=$?
grep -n "error\|FAILED" work/run_nvn4/build.txt | head -20
tail -2 work/run_nvn4/build.txt
exit $rc
