# Contributing

Thanks for helping. Bug reports with a good log are as useful as code. Small fixes can go straight to a pull request. For anything bigger, open an issue first so we can agree on the approach before you spend time on it.

## Which repository

| Repository | What goes there |
|---|---|
| [MetroidPrimeRemasteredRecomp](https://github.com/drakolordx7/MetroidPrimeRemasteredRecomp) (this one) | Game bugs, `game-build/`, the docs, the helper scripts in `` |
| [nxrecomp](https://github.com/drakolordx7/nxrecomp) | Code in `recomp/`, `runtime/` and `tools/`. It is included here as the `base` submodule. |

If you are not sure, file the issue here. We will move it.

## No game data, ever

Do not put any of these in an issue, a pull request, a log excerpt or a commit:

- game dumps (`.nsp`, `.xci`, `.nsz`, `.xcz`), keys (`prod.keys`, `title.keys`) or anything from your console
- files extracted from the game: `exefs`, `romfs`, `bc7_cache`, `shader_cache`, textures, models, audio, movies
- the generated C++ from the recompiler (`work/lift`), disassembly or decompiled game code, IDA databases
- anything in the git-ignored folders `game/` and `work/`

Screenshots and short clips of a bug in a running build are fine. Logs are fine. `setup.log` is written without key data, and you should skim any other file before you post it. Pull requests that contain game data are closed.

## How the code is laid out

The game is translated ahead of time. Each piece does one job:

| Part | Where | What it does |
|---|---|---|
| Recompiler | `recomp/` | Turns the game's AArch64 code into C++. It is checked against the Unicorn CPU emulator instruction by instruction. `recomp/games/mpr/` has the per-game settings and hook sites. |
| Runtime | `runtime/src/` | Everything the game expects from the console: memory map and module loader (`mem`, `loader`), threads and the SVC layer (`kernel`), C++ exceptions (`eh`), crash reports, log and freeze watchdog (`diag`), IPC (`ipc`). |
| Services | `runtime/src/services/` | The Horizon system services the game's SDK talks to: file system, saves, account, applet, input, time, audio renderer and others. One file per service group. |
| Graphics | `runtime/src/gfx/` | A Vulkan 1.3 renderer. `gfx/nvn/` implements the game's graphics API (NVN) on top of it. Play mode (window, controls, settings page) is in `gfx/play/`. |
| Media and timing | `runtime/src/media/`, `runtime/src/timestep/` | Movies on Windows Media Foundation. The frame step that makes high refresh rates work. |
| Tools | `tools/` | Offline tools: Maxwell shaders to SPIR-V, ASTC to BC7 textures, Tegra tiling, the setup tool (`setup/`), the release builder (`release/`), the boot loop (`boot/`) and the test tools (`test/`). |
| Game build | `game-build/` | The CMake project that links the runtime and the translated game into `mpr.exe`. |

Some docs are named `S3c.md`, `S4d.md` and so on. They are development logs. The letter and number are the project's work areas: S1 recompiler, S3 OS and services, S4 graphics, S5 test tooling, S6 boot, S8 play mode, S9 movies and audio, S10 display, S11 high refresh. `docs/PLAN.md` has the full list.

## Building and testing

Setup and build steps are in the [README](README.md). Run the tests that match what you changed. Run the whole group once before you open the pull request.

| You changed | Run |
|---|---|
| Runtime | `pwsh runtime\scripts\build.ps1 -Test` (one group: `-Filter <regex>`; one test program directly: `runtime\build\release\nxrt_tests.exe <group>`) |
| Recompiler | From `recomp\`: `python oracle\difftest\difftest.py all`, `python oracle\difftest\mutation.py`, `python oracle\e2e\run_e2e.py`, `python oracle\hooks\test_hooks.py` |
| Test or boot tools | `tools\.venv\Scripts\python -I -m unittest discover -s tools\test\tests` (from `tools\test`) |
| Setup tool | `pwsh -File tools\setup\scripts\build.ps1 -Test` |
| Anything the game runs on | `tools\.venv\Scripts\python tools\boot\boot.py`, then `tools\.venv\Scripts\python tools\test\run_suite.py tools\test\suites\boot.toml` (needs your own extracted game) |

Timing tests can fail on a busy machine. Rerun a failing one on its own before you call it broken.

Folders with an `oracle/LOCKED` file hold hash-locked reference checks (`oracle/SHA256SUMS`). Do not edit them in a pull request. If one is wrong, open an issue and explain why.

## Code style

Match the code around you. There is no formatter.

- C++20, built with clang-cl. Four-space indent, braces on the same line, lines up to about 140 columns. Names are `snake_case` for functions and variables, `kName` for constants, `g_` for globals and `t_` for thread-local state. Logging goes through `NXLOG_E/W/I/D/T`. Settings are read with `config_get_*`, and every new key is added to `runtime/docs/CONFIG.md`.
- Each file starts with a short comment that says what the file is for, and new files carry `SPDX-License-Identifier: GPL-3.0-or-later`. Comments explain why, not what.
- Python is plain and standard-library first, four-space indent, a docstring at the top with the usage, `argparse` for command lines.
- No inline assembly in the recompiler. Its output must be deterministic.
- Fix the mechanism behind a failure. A retry, a sleep or a special case for one asset does not count as a fix.
- Write docs in short, plain sentences.

## Commits and pull requests

- One logical change per commit. The first line is a plain imperative sentence of about 70 characters or fewer, such as `Fix texture binding in the hangar scene`. Use the body to say why. No tool or co-author trailers.
- Say in the pull request what you ran and what it showed. Link the issue it closes. The pull request template has a checklist.
- Keep unrelated clean-ups out of the same pull request.

## Reporting a bug with a log

Use the issue forms. The more of the following you attach, the faster it gets fixed.

- Your GPU, driver version and Windows version, and what you changed in `mpr.ini` or `controls.ini`.
- `mpr.log`, which is next to `mpr.exe`. The previous run is `mpr.log.prev`. For a startup problem, also send `setup.log` from the install folder.
- For a crash: `mpr_crash.txt` or `mpr_fatal.txt`, next to `mpr.exe`. For a freeze: `mpr_freeze.txt`. The watchdog writes it when the game stops making progress for 10 seconds.
- A screenshot of the bug in a running build.

For more detail, turn on the trace switches. Each is an `mpr.ini` key or an environment variable (the key `[section] name` becomes `NXRT_SECTION_NAME`). Every key is listed in [CONFIG.md](https://github.com/drakolordx7/nxrecomp/blob/main/runtime/docs/CONFIG.md).

| Switch | What it adds |
|---|---|
| `[log] level = trace` (`NXRT_LOG_LEVEL=trace`) | Every log line down to trace level. Valid values are `error`, `warn`, `info`, `debug` and `trace`. |
| `[hle] trace = nvn` (`NXRT_HLE_TRACE=nvn`) | An ordered log of every host-side call whose name starts with the given prefix, with arguments. `nvn` shows the graphics API calls. `trace_limit` caps the number of lines (default 20000). |
| `[nvn] trace_frame = N` (`NXRT_NVN_TRACE_FRAME=N`) | Every draw, clear and copy of presented frame N, with shaders, render targets and state. The other `[nvn] trace_*` keys are described in the [S4e log](https://github.com/drakolordx7/nxrecomp/blob/main/runtime/docs/S4e.md). |
| `[gfx] validation = true` (`NXRT_GFX_VALIDATION=1`) | Vulkan validation layer messages. Needs the Vulkan SDK. |

Trace output can be large. Trim it to the part around the bug, or attach it as a file.
