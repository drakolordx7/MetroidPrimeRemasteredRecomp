# S26: build every runtime test target of runtime-wt\play3 (nxrt_tests, nxrt_gfx_tests, the lift_* programs) in work\play3_layout\build_rt and run ctest.
#   pwsh .weaver\rel_tests.ps1 [-Filter re] [-NoBuild] [-BuildOnly] [-Clean] [-Jobs 2]
# work\play3_layout holds junctions recomp, runtime, tools, refs -> the play3 runtime worktree and the main recomp, tools, refs checkouts, because the lift tests and the gfx build expect ../recomp and ../tools
# next to the runtime. -Clean deletes the build folder first (the clean-build run of the stream report). NXRT_MOVIE_DIR is set for the movie tests when present.
param([string]$Filter = ".", [switch]$NoBuild, [switch]$BuildOnly, [switch]$Clean, [int]$Jobs = 2)
$ErrorActionPreference = "Stop"
$lay = "D:\AI\Active\Metroid-Prime\work\play3_layout"
$bd = Join-Path $lay "build_rt"
if ($Clean -and (Test-Path $bd)) { Remove-Item -Recurse -Force $bd }
$cfg = "cmake -S `"$lay\runtime`" -B `"$bd`" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DNXRT_BUILD_LIFT_TESTS=ON"
$cmd = "call D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd && "
if (-not $NoBuild) { $cmd += "$cfg && cmake --build `"$bd`"" }
if (-not $NoBuild -and -not $BuildOnly) { $cmd += " && " }
if (-not $BuildOnly) {
    if (Test-Path "D:\AI\Active\Metroid-Prime\work\media_fmv") { $cmd += "set NXRT_MOVIE_DIR=D:\AI\Active\Metroid-Prime\work\media_fmv&& " }
    $cmd += "set NXRT_NVN_SHADER_CACHE=D:\AI\Active\Metroid-Prime\work\shader_cache\spirv&& ctest --test-dir `"$bd`" --output-on-failure -j $Jobs -R `"$Filter`""
}
cmd /c $cmd
exit $LASTEXITCODE
