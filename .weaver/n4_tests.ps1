# S4h: build and run the CTest groups of the runtime-wt\nvn4 worktree (gfx on, lift tests off), at below-normal priority:
#   pwsh .weaver\n4_tests.ps1 [-Filter "regex"] [-NoBuild] [-BuildOnly] [-Jobs 2]
param([string]$Filter = ".", [switch]$NoBuild, [switch]$BuildOnly, [int]$Jobs = 2)
$ErrorActionPreference = "Stop"
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
$wt = "D:\AI\Active\Metroid-Prime\runtime-wt\nvn4"
$bd = Join-Path $wt "build\release"
$env_cmd = Join-Path $wt "scripts\env.cmd"
$cfg = "cmake -S `"$wt`" -B `"$bd`" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_BUILD_LIFT_TESTS=OFF -DNXRT_RECOMP_INCLUDE=D:\AI\Active\Metroid-Prime\recomp\include"
$cmd = "call `"$env_cmd`" && "
if (-not $NoBuild) { $cmd += "$cfg && cmake --build `"$bd`" --target nxrt_tests nxrt_gfx_tests" }
if (-not $NoBuild -and -not $BuildOnly) { $cmd += " && " }
if (-not $BuildOnly) { $cmd += "ctest --test-dir `"$bd`" --output-on-failure -j $Jobs -R `"$Filter`"" }
cmd /c $cmd
exit $LASTEXITCODE
