#!/bin/bash
# warm2_matrix.sh N -- S24 final matrix: N rounds of three cold conditions on the Frigate route (cap 60, one run at a time), each round with new SPIR-V salts:
#   A whole pipelines (gpl=0)   B pipeline libraries (defaults)   E libraries after a shader preparation (its pipeline cache file copied into the run folder)
# Results: work/prof/mx2_<cond><round>.* ; table: python .weaver/warm2_table.py --prefix mx2 A B E
cd /d/AI/Active/Metroid-Prime
N=${1:-3}
EXE=D:/AI/Active/Metroid-Prime/game-build-warm2/build/warm2/mpr.exe
for r in $(seq 1 $N); do
  bash .weaver/warm2_queue.sh "mx2_A$r:0:mx2A$r:0" > /dev/null 2>&1
  bash .weaver/warm2_queue.sh "mx2_B$r:1:mx2B$r:0" > /dev/null 2>&1
  rm -rf work/run_mx_prep; mkdir -p work/run_mx_prep; rm -f work/shader_cache/prepare.state
  ( cd work/run_mx_prep && NXRT_NVN_SHADER_CACHE=D:/AI/Active/Metroid-Prime/work/shader_cache/spirv NXRT_NVN_SPIRV_SALT=mx2E$r $EXE --prepare-shaders --log prep.log > prep.out 2>&1 )
  cp work/run_mx_prep/prep.out work/prof/mx2_E$r.prep.out
  CACHE_FROM=work/run_mx_prep bash .weaver/warm2_queue.sh "mx2_E$r:1:mx2E$r:0" > /dev/null 2>&1
done
echo matrix done > work/prof/mx2_done.txt
