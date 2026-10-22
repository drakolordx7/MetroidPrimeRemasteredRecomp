@echo off
rem Builds mpr.exe for the perf stream: runtime-wt\perf compiled in, game libraries from work\build\mpr_perf (.weaver\build_mpr_perf.cmd). Output game-build\build\perf\mpr.exe
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build" -B "%ROOT%\game-build\build\perf" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\perf" -DMPR_LIB_DIR="%ROOT%\work\build\mpr_perf" -DNXRT_RECOMP_INCLUDE="%ROOT%\recomp\include" || exit /b 1
cmake --build "%ROOT%\game-build\build\perf" --target mpr %*
exit /b %errorlevel%
