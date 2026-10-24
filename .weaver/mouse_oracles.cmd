@echo off
rem Recompiler oracles of the mouse worktree with the shared venv; every oracle in its own cmd (nx_env.cmd grows PATH on every call).
rem   .weaver\mouse_oracles.cmd [difftest] [mutation] [e2e] [hooks] [ka]   (default: all)
rem The worktree must have LF line endings (git -c core.autocrlf=false checkout-index -f -a): mutation.py matches multi-line text.
setlocal
set "PY=D:\AI\Active\Metroid-Prime\tools\.venv\Scripts\python.exe"
set "RC=D:\AI\Active\Metroid-Prime\work\mouse_layout\recomp"
cd /d %RC%
set "WHAT=%*"
if "%WHAT%"=="" set "WHAT=difftest mutation e2e hooks ka"
for %%o in (%WHAT%) do call :run %%o
exit /b 0
:run
echo === %1
if "%1"=="difftest" cmd /c "scripts\nx_env.cmd %PY% oracle\difftest\difftest.py all"
if "%1"=="mutation" cmd /c "scripts\nx_env.cmd %PY% oracle\difftest\mutation.py"
if "%1"=="e2e" cmd /c "scripts\nx_env.cmd %PY% oracle\e2e\run_e2e.py"
if "%1"=="hooks" cmd /c "scripts\nx_env.cmd %PY% oracle\hooks\test_hooks.py"
if "%1"=="ka" cmd /c "scripts\nx_env.cmd %PY% oracle\ka\run_ka.py"
echo %1 exit %errorlevel%
exit /b 0

