@echo off
rem S11: configure + build mpr.exe from the hifps runtime worktree and the re-lifted libs (work\build\mpr_hifps) into game-build\build\hifps.
rem After this one configure, `.weaver\hifps_wt.sh` (boot.py) rebuilds incrementally (the cache keeps MPR_LIB_DIR).
setlocal
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "B=%ROOT%\game-build\build\hifps"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build" -B "%B%" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\hifps" -DMPR_LIB_DIR="%ROOT%\work\build\mpr_hifps"
if errorlevel 1 exit /b 1
cmake --build "%B%" --target mpr
exit /b %errorlevel%
