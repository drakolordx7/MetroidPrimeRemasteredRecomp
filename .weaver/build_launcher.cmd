@echo off
rem S27: rebuild mpr.exe of the launcher worktree (after .weaver\cfg_launcher.cmd configured it) -> game-build-launcher\build\launcher\mpr.exe
setlocal
call "D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd"
cmake --build "D:\AI\Active\Metroid-Prime\game-build-launcher\build\launcher" --target mpr %*
exit /b %errorlevel%
