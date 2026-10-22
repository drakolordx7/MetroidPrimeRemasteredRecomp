@echo off
rem configure + build nxrt_tests of a runtime worktree: wt_build.cmd <worktree dir>
call D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd
cd /d %1
cmake -S . -B build\release -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_RECOMP_INCLUDE=D:\AI\Active\Metroid-Prime\recomp\include || exit /b 1
cmake --build build\release --target nxrt_tests
