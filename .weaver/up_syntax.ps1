# S23: syntax-check (no codegen, no link) sources of runtime-wt/upscale. pwsh .weaver\up_syntax.ps1 src\gfx\upscale\foo.cpp [more.cpp ...]
# Extra include dirs (SDK headers) are in the repo's third_party folders. Exit 0 = every file compiles.
param([Parameter(Mandatory, Position = 0, ValueFromRemainingArguments)][string[]]$Files)
$root = "D:\AI\Active\Metroid-Prime\runtime-wt\upscale"
$Build = "D:\AI\Active\Metroid-Prime\game-build-upscale\build\upscale"
$recomp = "D:/AI/Active/Metroid-Prime/recomp/include"
$inc = "/I`"$root\include`" /I`"$root\src\gfx`" /I`"$root\src\gfx\nvn`" /I`"$root\src\gfx\nvn\third_party`" /I`"$root\src\gfx\upscale\third_party`" /I`"$root\src\services`" /I`"$root\src\testtools`" /I`"$root\tests`" " +
       "/I`"$Build\_deps\sdl3-src\include`" /I`"$Build\_deps\imgui-src`" /I`"$Build\_deps\vulkan_headers-src\include`" /I`"$Build\_deps\volk-src`" /I`"$recomp`""
$env_cmd = "D:\AI\Active\Metroid-Prime\runtime\scripts\env.cmd"
$rc = 0
foreach ($f in $Files) {
    $p = if ([System.IO.Path]::IsPathRooted($f)) { $f } else { Join-Path $root $f }
    cmd /c "call `"$env_cmd`" >nul 2>&1 && clang-cl /nologo /std:c++20 /Zs /EHsc /W3 -Wno-unused-parameter -Wno-missing-field-initializers -Wno-cast-function-type-mismatch -Wno-cast-function-type-strict -Wno-language-extension-token /DNOMINMAX /DWIN32_LEAN_AND_MEAN /D_CRT_SECURE_NO_WARNINGS /D_WIN32_WINNT=0x0A00 $inc `"$p`""
    if ($LASTEXITCODE -ne 0) { $rc = 1 } else { Write-Host "OK $f" }
}
exit $rc
