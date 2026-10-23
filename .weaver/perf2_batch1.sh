#!/bin/bash
cd /d/AI/Active/Metroid-Prime
export MSYS2_ARG_CONV_EXCL='*'
.weaver/perf2_run.sh b120 120 --env NXRT_NVN_ACCEPT_UNLINKED=0
.weaver/perf2_run.sh fix120 120
