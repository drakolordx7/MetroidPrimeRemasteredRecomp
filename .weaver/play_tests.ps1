# Build and run the play-mode CTest groups of the runtime-wt\play worktree (gfx on, lift tests off):
#   pwsh .weaver\play_tests.ps1 [-Filter "play_|tt_|svc_hid|gfx_platform"] [-NoBuild]
# Builds nxrt_tests and nxrt_gfx_tests into runtime-wt\play\build\release (sccache) and runs ctest. Hidden windows (NXRT_GFX_HIDDEN=1 is set by the test entries).
param([string]$Filter = "play_|tt_|hid|gfx_platform|gfx_limiter|gfx_overlay|hooks", [switch]$NoBuild)
$ErrorActionPreference = "Stop"
$wt = "D:\AI\Active\Metroid-Prime\runtime-wt\play"
$bd = Join-Path $wt "build\release"
$env_cmd = Join-Path $wt "scripts\env.cmd"
$cfg = "cmake -S `"$wt`" -B `"$bd`" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_BUILD_LIFT_TESTS=OFF -DNXRT_RECOMP_INCLUDE=D:\AI\Active\Metroid-Prime\recomp\include"
$cmd = "call `"$env_cmd`" && "
if (-not $NoBuild) { $cmd += "$cfg && cmake --build `"$bd`" --target nxrt_tests nxrt_gfx_tests && " }
$cmd += "ctest --test-dir `"$bd`" --output-on-failure -R `"$Filter`""
cmd /c $cmd
exit $LASTEXITCODE
