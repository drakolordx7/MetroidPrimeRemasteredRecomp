# Build and run the CTest groups of the runtime-wt\perf2 worktree (gfx on, lift tests off):
#   pwsh .weaver\perf2_tests.ps1 [-Filter "regex"] [-NoBuild]     (default filter: everything)
param([string]$Filter = ".", [switch]$NoBuild)
$ErrorActionPreference = "Stop"
$wt = "D:\AI\Active\Metroid-Prime\runtime-wt\perf2"
$bd = Join-Path $wt "build\release"
$env_cmd = Join-Path $wt "scripts\env.cmd"
$cfg = "cmake -S `"$wt`" -B `"$bd`" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_BUILD_LIFT_TESTS=OFF -DNXRT_RECOMP_INCLUDE=D:\AI\Active\Metroid-Prime\recomp\include"
$cmd = "call `"$env_cmd`" && "
if (-not $NoBuild) { $cmd += "$cfg && cmake --build `"$bd`" --target nxrt_tests nxrt_gfx_tests && " }
$cmd += "ctest --test-dir `"$bd`" --output-on-failure -R `"$Filter`""
cmd /c $cmd
exit $LASTEXITCODE
