# Build and run the CTest groups of the runtime-wt\stab worktree against the recomp-wt\stab headers (lift tests off: they need ../recomp next to the runtime):
#   pwsh .weaver\stab_tests.ps1 [-Filter re] [-NoBuild] [-BuildOnly]
param([string]$Filter = ".", [switch]$NoBuild, [switch]$BuildOnly)
$ErrorActionPreference = "Stop"
$wt = "D:\AI\Active\Metroid-Prime\runtime-wt\stab"
$bd = Join-Path $wt "build\release"
$env_cmd = Join-Path $wt "scripts\env.cmd"
$cfg = "cmake -S `"$wt`" -B `"$bd`" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_BUILD_LIFT_TESTS=OFF -DNXRT_RECOMP_INCLUDE=D:\AI\Active\Metroid-Prime\recomp-wt\stab\include"
$cmd = "call `"$env_cmd`" && "
if (-not $NoBuild) { $cmd += "$cfg && cmake --build `"$bd`" --target nxrt_tests nxrt_gfx_tests" }
if (-not $NoBuild -and -not $BuildOnly) { $cmd += " && " }
if (-not $BuildOnly) { $cmd += "ctest --test-dir `"$bd`" --output-on-failure -R `"$Filter`"" }
cmd /c $cmd
exit $LASTEXITCODE
