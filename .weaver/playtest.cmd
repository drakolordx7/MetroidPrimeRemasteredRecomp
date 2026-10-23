@echo off
rem Play the current build in a window (snapshot in work\playtest, so later rebuilds don't touch it).
rem Refresh the snapshot: copy game-build\build\release\*.exe and *.dll into work\playtest.
set ROOT=%~dp0..
set NXRT_FS_ROMFS=%ROOT%\game\romfs
set NXRT_FS_SAVE_DIR=%ROOT%\work\playtest\save
set NXRT_NVN_SHADER_CACHE=%ROOT%\work\shader_cache\spirv
set NXRT_NVN_BC7_CACHE=%ROOT%\work\run\bc7_cache
set NXRT_NVN_PIPELINE_CACHE=%ROOT%\work\playtest\pipeline_cache.bin
cd /d "%ROOT%\work\playtest"
start "" mpr.exe --log nxrt.log
