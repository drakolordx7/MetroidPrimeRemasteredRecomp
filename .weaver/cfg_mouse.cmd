@echo off
rem S28: configure + build mpr.exe from runtime-wt\mouse against the lifted libraries of work\build\mpr_mouse (recomp-wt\mouse sites) into game-build-mouse\build\mouse. Args go to the build.
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build-mouse" -B "%ROOT%\game-build-mouse\build\mouse" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\mouse" -DMPR_LIB_DIR="%ROOT%\work\build\mpr_mouse" -DNXRT_RECOMP_INCLUDE="%ROOT%\recomp-wt\mouse\include" -DNXRT_TOOLS_DIR="%ROOT%\tools" -DFETCHCONTENT_SOURCE_DIR_VOLK=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/volk-src -DFETCHCONTENT_SOURCE_DIR_VULKAN_HEADERS=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/vulkan_headers-src || exit /b 1
cmake --build "%ROOT%\game-build-mouse\build\mouse" --target mpr %*
exit /b %errorlevel%
