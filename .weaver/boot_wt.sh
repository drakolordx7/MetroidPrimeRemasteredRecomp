#!/bin/bash
# boot.py against the boot2 runtime worktree (separate build dir game-build/build/boot2): .weaver/boot_wt.sh [boot.py args]
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\boot2' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build\build\boot2' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python tools/boot/boot.py "$@"
