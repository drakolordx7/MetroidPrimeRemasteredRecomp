@echo off
rem warm2: rebuild mpr.exe of the warm2 worktree (after .weaver\cfg_warm2.cmd configured it) -> game-build-warm2\build\warm2\mpr.exe
setlocal
call "D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd"
cmake --build "D:\AI\Active\Metroid-Prime\game-build-warm2\build\warm2" --target mpr %*
exit /b %errorlevel%
