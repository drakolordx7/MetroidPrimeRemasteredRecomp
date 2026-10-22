#!/bin/bash
# S13: boot.py (no rebuild) against the verify build, running in work/run_verify (own log/shots): .weaver/verify_boot.sh [boot.py args]
export MPR_BUILD_DIR='D:\AI\Active\Metroid-Prime\game-build-verify\build\verify' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime && exec tools/.venv/Scripts/python .weaver/boot_verify.py --no-build "$@"
