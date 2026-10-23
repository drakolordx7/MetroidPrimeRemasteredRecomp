#!/bin/bash
# S20 sweep against the stab build, own output folder: .weaver/stab_sweep.sh [sweep.py args]   (OUT=work/sweep_stab by default)
export NXRT_NVN_SHADER_CACHE='D:\AI\Active\Metroid-Prime\work\shader_cache\spirv' MSYS2_ARG_CONV_EXCL='*'
OUT=${OUT:-work/sweep_stab}
cd /d/AI/Active/Metroid-Prime && export MPR_ROOT=D:/AI/Active/Metroid-Prime; exec tools/.venv/Scripts/python tools-wt/stab/test/sweep.py --exe ${EXE:-game-build-stab/build/stab/mpr.exe} --out "$OUT" --md "$OUT/SWEEP.md" --cache work/sweep_cache_stab/bc7 "$@"
