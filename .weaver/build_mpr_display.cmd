@echo off
rem Lift and build the game libraries into work\lift_display and work\build\mpr_display (a private copy for the display stream; the shared
rem work\lift and work\build\mpr are left alone). Uses the current recomp\games\mpr\main.sites.   .weaver\build_mpr_display.cmd [-j N]
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
set "HERE=%ROOT%\recomp\scripts\"
set "MPR_BUILD=%ROOT%\work\build\mpr_display"
set "SCCACHE_DIR=%ROOT%\work\build\sccache"
set "SCCACHE_SERVER_PORT=24339"
set "SCCACHE_CACHE_SIZE=20G"
call "%HERE%nx_env.cmd" cmake -S "%HERE%..\games\mpr" -B "%MPR_BUILD%" -G Ninja -DCMAKE_TOOLCHAIN_FILE="%HERE%..\cmake\clang-cl.cmake" -DCMAKE_BUILD_TYPE=Release -DMPR_ROOT="%ROOT%" -DMPR_GEN="%ROOT%\work\lift_display"
if errorlevel 1 exit /b 1
call "%HERE%nx_env.cmd" cmake --build "%MPR_BUILD%" --target mpr_modules -- -j 16 %*
exit /b %errorlevel%
