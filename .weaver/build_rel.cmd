@echo off
rem build mpr.exe of the rel game build (game-build-rel\build\rel\mpr.exe); extra args go to cmake --build, e.g. --target mpr
call D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd
cmake --build D:\AI\Active\Metroid-Prime\game-build-rel\build\rel --target mpr %*
exit /b %errorlevel%
