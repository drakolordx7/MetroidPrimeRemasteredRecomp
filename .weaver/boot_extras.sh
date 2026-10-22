#!/bin/bash
# boot.py against the extras runtime worktree (build dir game-build/build/extras): .weaver/boot_extras.sh [boot.py args]
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\extras' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build\build\extras' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python .weaver/boot_extras.py "$@"
