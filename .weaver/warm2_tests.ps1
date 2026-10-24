# S24: build and run the CTest groups of the runtime-wt\warm2 worktree (gfx on, lift tests off):
#   pwsh .weaver\warm2_tests.ps1 [-Filter "regex"] [-NoBuild] [-Jobs 2]
# Builds nxrt_tests and nxrt_gfx_tests into runtime-wt\warm2\build\release (sccache) and runs ctest. The default filter runs every test.
# Hidden windows (NXRT_GFX_HIDDEN=1 is set by the test entries). Movie tests need NXRT_MOVIE_DIR (tools\media\movie_oracle.py fills work\media_fmv).
param([string]$Filter = ".", [switch]$NoBuild, [int]$Jobs = 2)
$ErrorActionPreference = "Stop"
$wt = "D:\AI\Active\Metroid-Prime\runtime-wt\warm2"
$bd = Join-Path $wt "build\release"
$env_cmd = Join-Path $wt "scripts\env.cmd"
$cfg = "cmake -S `"$wt`" -B `"$bd`" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_BUILD_LIFT_TESTS=OFF -DNXRT_RECOMP_INCLUDE=D:\AI\Active\Metroid-Prime\recomp\include"
$cmd = "call `"$env_cmd`" && "
if (-not $NoBuild) { $cmd += "$cfg && cmake --build `"$bd`" --target nxrt_tests nxrt_gfx_tests mpr_launcher mpr_launcher_tests && " }
$cmd += "set NXRT_MOVIE_DIR=D:\AI\Active\Metroid-Prime\work\media_fmv&& set NXRT_NVN_SHADER_CACHE=D:\AI\Active\Metroid-Prime\work\shader_cache\spirv&& ctest --test-dir `"$bd`" --output-on-failure -j $Jobs -R `"$Filter`""
cmd /c $cmd
exit $LASTEXITCODE
