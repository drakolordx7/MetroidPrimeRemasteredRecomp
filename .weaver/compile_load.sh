#!/bin/bash
# A realistic CPU load for audio timing runs: a clean rebuild of a runtime worktree's tests: .weaver/compile_load.sh <worktree dir, default runtime-wt/media-audio>
wt=${1:-D:/AI/Active/Metroid-Prime/runtime-wt/media-audio}
cd "$wt" && cmd //c "call scripts\env.cmd >nul 2>&1 && ninja -C build\release -t clean >nul 2>&1 && cmake --build build\release --target nxrt_tests >nul 2>&1"
