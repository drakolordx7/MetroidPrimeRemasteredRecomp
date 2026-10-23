@echo off
rem S21: configure + build mpr.exe from runtime-wt\stutter against work\build\mpr_perf into game-build-stutter\build\stutter. Args go to the build (e.g. -j 8).
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build-stutter" -B "%ROOT%\game-build-stutter\build\stutter" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\stutter" -DMPR_LIB_DIR="%ROOT%\work\build\mpr_perf" -DNXRT_RECOMP_INCLUDE="%ROOT%\recomp\include" -DFETCHCONTENT_SOURCE_DIR_VOLK=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/volk-src -DFETCHCONTENT_SOURCE_DIR_VULKAN_HEADERS=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/vulkan_headers-src || exit /b 1
cmake --build "%ROOT%\game-build-stutter\build\stutter" --target mpr %*
exit /b %errorlevel%
