@echo off
rem build one target of a runtime worktree: wt_target.cmd <worktree dir> <target>
call D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd
cd /d %1
cmake --build build\release --target %2
