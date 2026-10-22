#!/bin/bash
# S13: copy the verify build to game-build-verify/build/snap (what the scripted-run tools run, so a rebuild is never blocked by a live exe): .weaver/verify_snap.sh
cd /d/AI/Active/Metroid-Prime/game-build-verify/build && mkdir -p snap && cp -f verify/mpr.exe verify/*.dll snap/ 2>/dev/null; ls -la snap | head
