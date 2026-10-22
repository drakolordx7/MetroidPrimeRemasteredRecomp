@echo off
rem Builds mpr.exe for the extras stream: runtime-wt\extras compiled in, game libraries from work\build\mpr_extras (.weaver\build_mpr_extras.cmd). Output game-build\build\extras\mpr.exe
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build" -B "%ROOT%\game-build\build\extras" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\extras" -DMPR_LIB_DIR="%ROOT%\work\build\mpr_extras" -DNXRT_RECOMP_INCLUDE="%ROOT%\recomp\include" || exit /b 1
cmake --build "%ROOT%\game-build\build\extras" --target mpr %*
exit /b %errorlevel%
