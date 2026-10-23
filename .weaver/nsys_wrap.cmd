@echo off
rem nsys_wrap.cmd <mpr args> -- runs the perf2 mpr.exe under Nsight Systems for the gameplay window (used with prof_run.py --exe); output work\prof\nsys_<tag>.nsys-rep
set "NSYS=C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.5.1\target-windows-x64\nsys.exe"
"%NSYS%" profile --trace=wddm --sample=none --cpuctxsw=none --delay=%NSYS_DELAY% --duration=%NSYS_DURATION% --force-overwrite=true -o D:\AI\Active\Metroid-Prime\work\prof\%NSYS_TAG% D:\AI\Active\Metroid-Prime\game-build\build\perf2\mpr.exe %*
