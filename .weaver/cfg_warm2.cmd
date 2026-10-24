@echo off
rem warm2: configure + build mpr.exe from runtime-wt\warm2 against work\build\mpr into game-build-warm2\build\warm2. Args go to the build (e.g. -j 6).
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build-warm2" -B "%ROOT%\game-build-warm2\build\warm2" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\warm2" -DMPR_LIB_DIR="%ROOT%\work\build\mpr" -DNXRT_RECOMP_INCLUDE="%ROOT%\recomp\include" -DNXRT_TOOLS_DIR="%ROOT%\tools" -DNXRT_A2B_DIR="%ROOT%\tools\textures\build\release" -DFETCHCONTENT_SOURCE_DIR_VOLK=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/volk-src -DFETCHCONTENT_SOURCE_DIR_VULKAN_HEADERS=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/vulkan_headers-src -DFETCHCONTENT_SOURCE_DIR_SDL3=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/sdl3-src -DFETCHCONTENT_SOURCE_DIR_VMA=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/vma-src -DFETCHCONTENT_SOURCE_DIR_IMGUI=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/imgui-src || exit /b 1
cmake --build "%ROOT%\game-build-warm2\build\warm2" --target mpr %*
exit /b %errorlevel%
