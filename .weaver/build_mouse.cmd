@echo off
rem S28: rebuild mpr.exe of the mouse worktree (after .weaver\cfg_mouse.cmd configured it) -> game-build-mouse\build\mouse\mpr.exe
setlocal
call "D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd"
cmake --build "D:\AI\Active\Metroid-Prime\game-build-mouse\build\mouse" --target mpr %*
exit /b %errorlevel%
