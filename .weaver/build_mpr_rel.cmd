@echo off
rem Lift and build the game libraries into work\lift_rel and work\build\mpr_rel from the recomp worktree recomp-wt\rel (private copy; the shared
rem work\lift and work\build\mpr are left alone). Uses that worktree's main.sites.   .weaver\build_mpr_rel.cmd [-j N]
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
set "RC=%ROOT%\recomp-wt\rel"
set "HERE=%RC%\scripts\"
set "MPR_BUILD=%ROOT%\work\build\mpr_rel"
set "SCCACHE_DIR=%ROOT%\work\build\sccache"
set "SCCACHE_SERVER_PORT=24339"
set "SCCACHE_CACHE_SIZE=20G"
call "%HERE%nx_env.cmd" cmake -S "%RC%\games\mpr" -B "%MPR_BUILD%" -G Ninja -DCMAKE_TOOLCHAIN_FILE="%RC%\cmake\clang-cl.cmake" -DCMAKE_BUILD_TYPE=Release -DMPR_ROOT="%ROOT%" -DNX_PYTHON=D:/AI/Active/Metroid-Prime/tools/.venv/Scripts/python.exe -DMPR_GEN="%ROOT%\work\lift_rel"
if errorlevel 1 exit /b 1
call "%HERE%nx_env.cmd" cmake --build "%MPR_BUILD%" --target mpr_modules -- -j 12 %*
exit /b %errorlevel%
