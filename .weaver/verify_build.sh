#!/bin/bash
# S13: build mpr.exe from the verify runtime worktree into game-build-verify/build/verify (private game-build copy at HEAD): .weaver/verify_build.sh
export MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime && exec pwsh -NoProfile -File game-build-verify/scripts/build.ps1 -Runtime 'D:\AI\Active\Metroid-Prime\runtime-wt\verify' -Out 'D:\AI\Active\Metroid-Prime\game-build-verify\build\verify'
