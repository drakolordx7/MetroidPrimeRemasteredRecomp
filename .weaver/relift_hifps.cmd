@echo off
rem S11: re-lift + build mpr_main with the current recomp\games\mpr\main.sites into work\lift_hifps / work\build\mpr_hifps
rem (the shared work\lift and work\build\mpr stay untouched). Needs mpr_sdk/subsdk0/rtld libs: copied from work\build\mpr by libs_hifps step below.
setlocal
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "HERE=%ROOT%\recomp\scripts\"
if not defined MPR_JOBS set "MPR_JOBS=20"
if not defined SCCACHE_DIR set "SCCACHE_DIR=%ROOT%\work\build\sccache"
if not defined SCCACHE_SERVER_PORT set "SCCACHE_SERVER_PORT=24339"
if not defined SCCACHE_CACHE_SIZE set "SCCACHE_CACHE_SIZE=20G"
set "B=%ROOT%\work\build\mpr_hifps"
call "%HERE%nx_env.cmd" cmake -S "%ROOT%\recomp\games\mpr" -B "%B%" -G Ninja -DCMAKE_TOOLCHAIN_FILE="%ROOT%\recomp\cmake\clang-cl.cmake" -DCMAKE_BUILD_TYPE=Release -DMPR_ROOT="%ROOT%" -DMPR_GEN="%ROOT%\work\lift_hifps"
if errorlevel 1 exit /b 1
call "%HERE%nx_env.cmd" cmake --build "%B%" --target mpr_main -- -j %MPR_JOBS% %*
if errorlevel 1 exit /b 1
for %%L in (sdk subsdk0 rtld) do copy /Y "%ROOT%\work\build\mpr\mpr_%%L.lib" "%B%\" >nul
exit /b 0
