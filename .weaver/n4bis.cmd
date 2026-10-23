@echo off
rem S4g: build mpr.exe from runtime-wt\bis_<X> (a detached worktree at one commit) into game-build-nvn4\build\bis_<X>   .weaver\n4bis.cmd A
setlocal
set "ROOT=D:\AI\Active\Metroid-Prime"
set "B=%ROOT%\game-build-nvn4\build\bis_%1"
call "%ROOT%\runtime\scripts\env.cmd"
cmake -S "%ROOT%\game-build-nvn4" -B "%B%" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_C_COMPILER_LAUNCHER=sccache -DCMAKE_CXX_COMPILER_LAUNCHER=sccache -DMPR_RUNTIME_DIR="%ROOT%\runtime-wt\bis_%1" > "%ROOT%\work\n4\bis_%1.txt" 2>&1
if errorlevel 1 exit /b 1
cmake --build "%B%" --target mpr >> "%ROOT%\work\n4\bis_%1.txt" 2>&1
exit /b %errorlevel%
