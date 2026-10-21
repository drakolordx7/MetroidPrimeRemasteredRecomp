# Verifies every Phase 0 tool is present and runs. Usage: pwsh .weaver\check-toolchain.ps1
$root = Split-Path $PSScriptRoot -Parent
$fail = 0
function Check($name, [scriptblock]$probe) {
    try { $out = (& $probe 2>&1 | Out-String).Trim().Split("`n")[0]; if ($LASTEXITCODE -gt 1) { throw $out }; "PASS  {0,-14} {1}" -f $name, $out }
    catch { "FAIL  {0,-14} {1}" -f $name, $_; $script:fail++ }
}
$links = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
$sdk = (Get-ChildItem C:\VulkanSDK -Directory | Sort-Object Name -Descending | Select-Object -First 1).FullName
$cdb = (Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WindowsApps", "C:\Program Files\WindowsApps" -Recurse -Filter cdb.exe -ErrorAction SilentlyContinue | Where-Object FullName -match 'amd64|x64' | Select-Object -First 1).FullName
Check clang-cl   { & "C:\Program Files\LLVM\bin\clang-cl.exe" --version }
Check cmake      { & "C:\Program Files\CMake\bin\cmake.exe" --version }
Check ninja      { & "$links\ninja.exe" --version }
Check sccache    { & "$links\sccache.exe" --version }
Check spirv-val  { & "$sdk\Bin\spirv-val.exe" --version }
Check renderdoc  { & "C:\Program Files\RenderDoc\renderdoccmd.exe" version }
Check cdb        { if (-not $cdb) { throw "cdb.exe not found" }; $cdb }
Check vcvars     { $v = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"; if (-not (Test-Path $v)) { throw "missing" }; $v }
Check dotnet10   { dotnet --list-sdks | Select-String '^10\.' }
Check cargo      { & "$env:USERPROFILE\.cargo\bin\cargo.exe" --version }
Check hactool    { & "$root\toolchain\hactool\hactool.exe" 2>&1 | Select-String 'hactool \(c\)' }
Check nstool     { & "$root\toolchain\nstool\nstool.exe" 2>&1 | Select-String 'NSTool' }
Check nx2elf     { & "$root\toolchain\nx2elf\nx2elf.exe" 2>&1 | Select-String 'Usage' }
Check retrotool  { & "$root\toolchain\retrotool\retrotool.exe" --version }
Check py-oracle  { & "$root\tools\.venv\Scripts\python.exe" -c "import unicorn, capstone, lz4, elftools; print('unicorn', unicorn.__version__, 'capstone', capstone.__version__)" }
Check eden       { if (-not (Test-Path "$root\toolchain\eden\eden.exe")) { throw "eden.exe missing" }; "Eden v0.2.1" }
Check guard      { python "$root\.claude\hooks\test_guard.py" | Select-Object -Last 1 }
Check ida        { if (-not (Test-Path "C:\Program Files\IDA Professional 9.4\idalib.dll")) { throw "idalib missing" }; "IDA 9.4 idalib present" }
"`n$fail failure(s)"; exit $fail
