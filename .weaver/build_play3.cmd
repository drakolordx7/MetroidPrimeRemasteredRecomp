@echo off
rem S26: rebuild mpr.exe of the play3 worktree (after .weaver\cfg_play3.cmd configured it) -> game-build-play3\build\play3\mpr.exe
setlocal
call "D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd"
cmake --build "D:\AI\Active\Metroid-Prime\game-build-play3\build\play3" --target mpr %*
exit /b %errorlevel%
