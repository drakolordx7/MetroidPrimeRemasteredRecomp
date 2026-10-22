@echo off
rem S13: point the verify mpr.exe build at the privately re-lifted libraries (work\build\mpr_verify) and build it.
setlocal
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build-verify" -B "%ROOT%\game-build-verify\build\verify" -DMPR_LIB_DIR="%ROOT%\work\build\mpr_verify" -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\verify"
if errorlevel 1 exit /b 1
cmake --build "%ROOT%\game-build-verify\build\verify" --target mpr
exit /b %errorlevel%
