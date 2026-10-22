#!/bin/bash
# boot.py against the media runtime worktree; builds game-build-media (a copy of game-build at HEAD), build dir game-build-media/build, run dir work/run_media:
#   .weaver/boot_media.sh [boot.py args]
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\media' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build-media\build' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python .weaver/boot_media.py "$@"
