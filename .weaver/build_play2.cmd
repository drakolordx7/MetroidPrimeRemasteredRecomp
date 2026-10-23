@echo off
rem S25: rebuild mpr.exe of the play2 worktree (after .weaver\cfg_play2.cmd configured it) -> game-build-play2\build\play2\mpr.exe
setlocal
call "D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd"
cmake --build "D:\AI\Active\Metroid-Prime\game-build-play2\build\play2" --target mpr %*
exit /b %errorlevel%
