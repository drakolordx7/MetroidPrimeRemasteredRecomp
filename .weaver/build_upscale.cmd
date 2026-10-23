@echo off
rem S23: rebuild mpr.exe of the upscale worktree (after .weaver\cfg_upscale.cmd configured it) -> game-build-upscale\build\upscale\mpr.exe
setlocal
call "D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd"
cmake --build "D:\AI\Active\Metroid-Prime\game-build-upscale\build\upscale" --target mpr %*
exit /b %errorlevel%
