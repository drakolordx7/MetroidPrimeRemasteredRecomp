@echo off
rem S28: re-lift + build mpr_main with recomp-wt\mouse\games\mpr\main.sites into work\lift_mouse / work\build\mpr_mouse (the shared work\lift and work\build\mpr stay untouched).
rem sdk, subsdk0 and rtld libraries are copied from work\build\mpr (they do not depend on main.sites).
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
set "RC=%ROOT%\recomp-wt\mouse"
set "HERE=%RC%\scripts\"
if not defined MPR_JOBS set "MPR_JOBS=20"
set "SCCACHE_DIR=%ROOT%\work\build\sccache"
set "SCCACHE_SERVER_PORT=24339"
set "SCCACHE_CACHE_SIZE=20G"
set "B=%ROOT%\work\build\mpr_mouse"
call "%HERE%nx_env.cmd" cmake -S "%RC%\games\mpr" -B "%B%" -G Ninja -DCMAKE_TOOLCHAIN_FILE="%RC%\cmake\clang-cl.cmake" -DCMAKE_BUILD_TYPE=Release -DMPR_ROOT="%ROOT%" -DMPR_GEN="%ROOT%\work\lift_mouse"
if errorlevel 1 exit /b 1
call "%HERE%nx_env.cmd" cmake --build "%B%" --target mpr_main -- -j %MPR_JOBS% %*
if errorlevel 1 exit /b 1
for %%L in (sdk subsdk0 rtld) do copy /Y "%ROOT%\work\build\mpr\mpr_%%L.lib" "%B%\" >nul
exit /b 0
