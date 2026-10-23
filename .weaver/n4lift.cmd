@echo off
rem S4g: lift + build mpr_main with the private sites file work\n4\mprgame\main.sites (current recomp main.sites + the particle-update site) into work\lift_n4 / work\build\mpr_n4.
rem The shared work\lift and work\build\mpr stay untouched; sdk/subsdk0/rtld libs are copied from work\build\mpr.   .weaver\n4lift.cmd [ninja args]
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
set "HERE=%ROOT%\recomp\scripts\"
if not defined MPR_JOBS set "MPR_JOBS=16"
set "SCCACHE_DIR=%ROOT%\work\build\sccache"
set "SCCACHE_SERVER_PORT=24339"
set "SCCACHE_CACHE_SIZE=20G"
set "B=%ROOT%\work\build\mpr_n4"
call "%HERE%nx_env.cmd" cmake -S "%ROOT%\work\n4\mprgame" -B "%B%" -G Ninja -DCMAKE_TOOLCHAIN_FILE="%ROOT%\recomp\cmake\clang-cl.cmake" -DCMAKE_BUILD_TYPE=Release -DMPR_ROOT="%ROOT%" -DMPR_GEN="%ROOT%\work\lift_n4"
if errorlevel 1 exit /b 1
call "%HERE%nx_env.cmd" cmake --build "%B%" --target mpr_main -- -j %MPR_JOBS% %*
if errorlevel 1 exit /b 1
for %%L in (sdk subsdk0 rtld) do copy /Y "%ROOT%\work\build\mpr\mpr_%%L.lib" "%B%\" >nul
exit /b 0
