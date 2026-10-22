#!/bin/bash
# boot.py against the prompts runtime worktree (build game-build/build/prompts, run dir work/run_prompts): .weaver/boot_prompts.sh [boot.py args]
export MPR_RUNTIME='D:\AI\Active\Metroid-Prime\runtime-wt\prompts' MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build\build\prompts' MSYS2_ARG_CONV_EXCL='*'
mkdir -p /d/AI/Active/Metroid-Prime/work/run_prompts
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python .weaver/boot_prompts.py "$@"
