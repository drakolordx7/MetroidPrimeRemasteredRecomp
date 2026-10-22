#!/bin/bash
# boot.py against the play runtime worktree (build dir game-build/build/play): .weaver/boot_play.sh [boot.py args]
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\play' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build\build\play' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python tools/boot/boot.py "$@"
