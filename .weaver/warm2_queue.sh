#!/bin/bash
# warm2_queue.sh -- runs the cold/warm matrix one run at a time. usage: warm2_queue.sh "TAG:GPL:SALT:SEED[:EXTRA]" ...  (SALT '-' = none; EXTRA = K=V,K=V)
cd /d/AI/Active/Metroid-Prime
for spec in "$@"; do
  IFS=: read tag gpl salt seed extra <<< "$spec"
  [ "$salt" = "-" ] && salt=""
  ex="NXRT_NVN_GPL=$gpl ${extra//,/ }"
  echo "== $tag gpl=$gpl salt=$salt seed=$seed extra=$extra"
  SALT=$salt SEED=$seed EXTRA="$ex" CACHE_FROM="$CACHE_FROM" bash .weaver/warm2_run.sh $tag 60 > work/prof/$tag.console 2>&1
  cat work/prof/$tag.sum.txt work/prof/$tag.warm.txt | grep -v "^run"
done
