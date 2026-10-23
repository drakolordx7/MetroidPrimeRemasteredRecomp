@echo off
rem S4g: build mpr.exe from runtime-wt\nvn4 against the privately lifted libs (work\build\mpr_n4) into game-build-nvn4\build\n4p
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
set "B=%ROOT%\game-build-nvn4\build\n4p"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build-nvn4" -B "%B%" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\nvn4" -DMPR_LIB_DIR="%ROOT%\work\build\mpr_n4" > "%ROOT%\work\n4\build_p.txt" 2>&1
if errorlevel 1 exit /b 1
cmake --build "%B%" --target mpr >> "%ROOT%\work\n4\build_p.txt" 2>&1
exit /b %errorlevel%
