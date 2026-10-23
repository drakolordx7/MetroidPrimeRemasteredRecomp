#!/bin/bash
# sweep.py with the shader cache set: .weaver/n4sweep.sh <outname> [sweep.py args]   (output work/n4/<outname>, log work/n4/<outname>.txt)
# EXE=<path to mpr.exe> (default work/n4/exe_base/mpr.exe, a copy of the baseline build so rebuilding does not clash); JOBS=<n> (default 1)
OUT=$1; shift
export NXRT_NVN_SHADER_CACHE='D:/AI/Active/Metroid-Prime/work/shader_cache/spirv' MSYS2_ARG_CONV_EXCL='*'
cd /d/AI/Active/Metroid-Prime
exec tools/.venv/Scripts/python tools/test/sweep.py --exe ${EXE:-work/n4/exe_base/mpr.exe} --jobs ${JOBS:-1} --no-confirm --out work/n4/$OUT --md work/n4/$OUT.md "$@" > work/n4/$OUT.txt 2>&1
