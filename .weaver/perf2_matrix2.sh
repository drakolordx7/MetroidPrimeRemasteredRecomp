#!/bin/bash
# perf2_matrix2.sh -- S18 second matrix: vsync (display paced), uncapped, Reflex on, old vs new on one exe
cd /d/AI/Active/Metroid-Prime
export MSYS2_ARG_CONV_EXCL='*'
OLD="--env NXRT_LATENCY_PACE=present --env NXRT_NVN_ACCEPT_UNLINKED=0 --env NXRT_NVN_POOL_VIEW=0"
echo "others: $(tasklist | grep -c mpr.exe)" > work/prof/m2.load
.weaver/perf2_run.sh m2_old_vs 0 $OLD --vsync
.weaver/perf2_run.sh m2_new_vs 0 --vsync
.weaver/perf2_run.sh m2_new_unc 0
.weaver/perf2_run.sh m2_new_refl60 60 --env NXRT_LATENCY_MODE=on
