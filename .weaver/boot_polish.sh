#!/bin/bash
# boot.py against the polish runtime worktree (build game-build-polish/build/polish, run dir work/run_polish): .weaver/boot_polish.sh [boot.py args]
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\polish' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build-polish\build\polish' MSYS2_ARG_CONV_EXCL='*'
mkdir -p /d/AI/Active/Metroid-Prime/work/run_polish
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python .weaver/boot_polish.py "$@"
