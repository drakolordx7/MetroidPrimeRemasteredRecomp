#!/bin/bash
# perf2_matrix.sh -- S18 before/after matrix on one exe, toggles by env: old = limiter in present + unlinked shader retry + slow pool import
cd /d/AI/Active/Metroid-Prime
export MSYS2_ARG_CONV_EXCL='*'
OLD="--env NXRT_LATENCY_PACE=present --env NXRT_NVN_ACCEPT_UNLINKED=0 --env NXRT_NVN_POOL_VIEW=0"
for cap in 60 120; do
  echo "others: $(tasklist | grep -c mpr.exe)" > work/prof/m_old$cap.load
  .weaver/perf2_run.sh m_old$cap $cap $OLD 
  echo "others: $(tasklist | grep -c mpr.exe)" > work/prof/m_new$cap.load
  .weaver/perf2_run.sh m_new$cap $cap 
done
