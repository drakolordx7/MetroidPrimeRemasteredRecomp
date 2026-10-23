@echo off
rem The lift_* runtime tests against the stab recompiler: they need ../recomp and ../tools next to the runtime, so they build from work\stab_layout (junctions).
call D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd
cmake -S D:\AI\Active\Metroid-Prime\work\stab_layout\runtime -B D:\AI\Active\Metroid-Prime\work\stab_layout\build_rt -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_BUILD_LIFT_TESTS=ON
if errorlevel 1 exit /b 1
cmake --build D:\AI\Active\Metroid-Prime\work\stab_layout\build_rt 
if errorlevel 1 exit /b 1
ctest --test-dir D:\AI\Active\Metroid-Prime\work\stab_layout\build_rt --output-on-failure -R "lift_"
