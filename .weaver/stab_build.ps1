# Configure (once, via cfg_stab.cmd) and build mpr.exe of the stab branch at below-normal priority: pwsh .weaver\stab_build.ps1
$env:MPR_RUNTIME = 'D:\AI\Active\Metroid-Prime\runtime-wt\stab'
$env:MPR_BUILD_DIR = 'D:\AI\Active\Metroid-Prime\game-build-stab\build\stab'
$p = Start-Process -FilePath pwsh -ArgumentList '-NoProfile','-File','D:\AI\Active\Metroid-Prime\game-build-stab\scripts\build.ps1' -PassThru -NoNewWindow -Wait
exit $p.ExitCode
