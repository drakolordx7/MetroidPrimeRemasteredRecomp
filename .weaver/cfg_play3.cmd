@echo off
rem S26: configure + build mpr.exe from runtime-wt\play3 against the lifted libraries of work\build\mpr into game-build-play3\build\play3. Args go to the build.
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build-play3" -B "%ROOT%\game-build-play3\build\play3" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\play3" -DMPR_LIB_DIR="%ROOT%\work\build\mpr" -DNXRT_RECOMP_INCLUDE="%ROOT%\recomp\include" -DNXRT_TOOLS_DIR="%ROOT%\tools" -DFETCHCONTENT_SOURCE_DIR_VOLK=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/volk-src -DFETCHCONTENT_SOURCE_DIR_VULKAN_HEADERS=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/vulkan_headers-src || exit /b 1
cmake --build "%ROOT%\game-build-play3\build\play3" --target mpr %*
exit /b %errorlevel%
