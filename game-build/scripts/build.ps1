# Configure + build mpr.exe into game-build\build\release (runtime sources are compiled in; the game libraries are imported).
# -Release builds the package flavour instead (MPR_RELEASE=ON: GUI program, ./exefs, no build paths in the files) into game-build\build\relpkg,
# together with mpr_launcher.exe: that is the folder tools\release\make_release.py packs.
param([string]$Config = "Release", [switch]$Clean, [switch]$Release, [string]$Runtime = $env:MPR_RUNTIME, [string]$Out = $env:MPR_BUILD_DIR)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$bd = if ($Out) { $Out } elseif ($Release) { Join-Path $root "build\relpkg" } else { Join-Path $root ("build\" + $Config.ToLower()) }
if ($Clean -and (Test-Path $bd)) { Remove-Item -Recurse -Force $bd }
$env_cmd = Join-Path $root "..\runtime\scripts\env.cmd"
$cfg = "cmake -S `"$root`" -B `"$bd`" -G Ninja -DCMAKE_BUILD_TYPE=$Config -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache"
if ($Runtime) { $cfg += " -DMPR_RUNTIME_DIR=`"$Runtime`"" }
$targets = "mpr"
if ($Release) { $cfg += " -DMPR_RELEASE=ON"; $targets = "mpr mpr_launcher" }
cmd /c "call `"$env_cmd`" && $cfg && cmake --build `"$bd`" --target $targets"
exit $LASTEXITCODE
