#!/bin/bash
# boot.py against the nvn3 runtime worktree; runs in work/run_nvn3: .weaver/boot_nvn3.sh [boot.py args]
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\nvn3' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build-nvn3\build\nvn3' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python .weaver/boot_nvn3.py "$@"
