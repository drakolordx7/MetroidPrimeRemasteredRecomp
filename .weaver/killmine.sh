#!/bin/bash
# kill only the mpr.exe of the nvn2 build tree (other streams run their own mpr.exe): .weaver/killmine.sh
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='mpr.exe'\" | Where-Object {\$_.ExecutablePath -like '*game-build-nvn2*'} | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
sleep 2
