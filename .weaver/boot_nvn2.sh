#!/bin/bash
# boot.py against the nvn2 runtime worktree; runs in work/run_nvn2 (own log/shots): .weaver/boot_nvn2.sh [boot.py args]
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\nvn2' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build-nvn2\build\nvn2' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python .weaver/boot_nvn2.py "$@"
