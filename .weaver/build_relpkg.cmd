@echo off
rem build the release-flavour mpr.exe of the rel game build (game-build-rel\build\relpkg\mpr.exe); run cfg_relpkg.cmd once first
call D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd
cmake --build D:\AI\Active\Metroid-Prime\game-build-rel\build\relpkg --target mpr %*
exit /b %errorlevel%
