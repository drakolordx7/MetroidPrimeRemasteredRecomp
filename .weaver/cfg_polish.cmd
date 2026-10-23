@echo off
rem one-time configure of the private polish game build
call D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd
cmake -S D:\AI\Active\Metroid-Prime\game-build-polish -B D:\AI\Active\Metroid-Prime\game-build-polish\build\polish -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR=D:\AI\Active\Metroid-Prime\runtime-wt\polish -DFETCHCONTENT_SOURCE_DIR_VOLK=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/volk-src -DFETCHCONTENT_SOURCE_DIR_VULKAN_HEADERS=D:/AI/Active/Metroid-Prime/game-build/build/release/_deps/vulkan_headers-src
