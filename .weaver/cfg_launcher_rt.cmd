@echo off
rem S27: configure the runtime test build of runtime-wt\launcher (work\launcher_layout\build_rt) and build only the targets named in %* (default: the launcher and its tests).
setlocal
set "LAY=D:\AI\Active\Metroid-Prime\work\launcher_layout"
call D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd
cmake -S "%LAY%\runtime" -B "%LAY%\build_rt" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_BUILD_LIFT_TESTS=ON || exit /b 1
if "%~1"=="" (cmake --build "%LAY%\build_rt" --target mpr_launcher mpr_launcher_tests) else (cmake --build "%LAY%\build_rt" --target %*)
exit /b %errorlevel%
