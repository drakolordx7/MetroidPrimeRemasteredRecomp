#!/bin/bash
# boot.py against the hifps runtime worktree (build dir game-build/build/hifps): .weaver/hifps_wt.sh [boot.py args]
export MPR_LIB_DIR=ignored; export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\hifps' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build\build\hifps' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python tools/boot/boot.py "$@"
