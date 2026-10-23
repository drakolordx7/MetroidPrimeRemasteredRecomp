@echo off
rem S21: rebuild mpr.exe of the stutter worktree (after .weaver\cfg_stutter.cmd configured it) -> game-build-stutter\build\stutter\mpr.exe
setlocal
call "D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd"
cmake --build "D:\AI\Active\Metroid-Prime\game-build-stutter\build\stutter" --target mpr %*
exit /b %errorlevel%
