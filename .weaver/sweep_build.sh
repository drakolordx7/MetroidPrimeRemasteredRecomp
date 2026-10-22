#!/bin/bash
# S15: build mpr.exe from the sweep runtime worktree into game-build-sweep/build/${1:-sweep} (private copy of the game libs in work/build/mpr_sweep)
OUT=${1:-sweep}
export MSYS2_ARG_CONV_EXCL='*' MPR_LIB_DIR='D:\AI\Active\Metroid-Prime\work\build\mpr_sweep'
cd /d/AI/Active/Metroid-Prime && exec pwsh -NoProfile -File game-build-sweep/scripts/build.ps1 -Runtime 'D:\AI\Active\Metroid-Prime\runtime-wt\sweep' -Out "D:/AI/Active/Metroid-Prime/game-build-sweep/build/$OUT"
