# Build a target of a runtime worktree and print only errors: pwsh .weaver\wtbuild.ps1 <worktree dir> [target]
param([string]$Dir, [string]$Target = "nxrt_tests")
Set-Location $Dir
$out = cmd /c "call scripts\env.cmd >nul 2>&1 && cmake --build build\release --target $Target 2>&1"
$out | Select-String -Pattern "error|FAILED|undefined" | Select-Object -First 40
"exit: $LASTEXITCODE"
