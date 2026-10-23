@echo off
rem S23: configure + build mpr.exe from runtime-wt\upscale against work\build\mpr_perf into game-build-upscale\build\upscale. Args go to the build (e.g. -j 8).
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build-upscale" -B "%ROOT%\game-build-upscale\build\upscale" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\upscale" -DMPR_LIB_DIR="%ROOT%\work\build\mpr_perf" -DNXRT_RECOMP_INCLUDE="%ROOT%\recomp\include" -DFETCHCONTENT_SOURCE_DIR_VOLK=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/volk-src -DFETCHCONTENT_SOURCE_DIR_VULKAN_HEADERS=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/vulkan_headers-src || exit /b 1
cmake --build "%ROOT%\game-build-upscale\build\upscale" --target mpr %*
exit /b %errorlevel%
