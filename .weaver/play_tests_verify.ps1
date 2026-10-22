# Build and run play/tt/hid/timestep CTest groups in runtime-wt\verify (gfx on, lift tests off): pwsh .weaver\play_tests_verify.ps1 [-Filter regex] [-NoBuild]
param([string]$Filter = "play_|tt_|hid|gfx_platform|gfx_limiter|gfx_overlay|hooks|timestep", [switch]$NoBuild)
$ErrorActionPreference = "Stop"
$wt = "D:\AI\Active\Metroid-Prime\runtime-wt\verify"
$bd = Join-Path $wt "build\release"
$env_cmd = Join-Path $wt "scripts\env.cmd"
$cfg = "cmake -S `"$wt`" -B `"$bd`" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_BUILD_LIFT_TESTS=OFF -DNXRT_RECOMP_INCLUDE=D:\AI\Active\Metroid-Prime\recomp\include"
$cmd = "call `"$env_cmd`" && "
if (-not $NoBuild) { $cmd += "$cfg && cmake --build `"$bd`" --target nxrt_tests nxrt_gfx_tests && " }
$cmd += "ctest --test-dir `"$bd`" --output-on-failure -R `"$Filter`""
cmd /c $cmd
exit $LASTEXITCODE
