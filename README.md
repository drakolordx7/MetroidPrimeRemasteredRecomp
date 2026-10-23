# Metroid Prime Remastered Recomp

A native Windows x64 port of Metroid Prime Remastered, made by statically recompiling the Nintendo Switch release (v1.0.0). It is not an emulator. The game's code is translated to C++ ahead of time and built into a normal Windows program. A runtime provides the Switch's operating system services, and the game's graphics API (NVN) runs on Vulkan.

This is an unofficial fan project. It is not affiliated with Nintendo or Retro Studios. The repository contains no game code, assets or keys, and you need your own copy of the game.

The recompiler, runtime and tools are in a separate repository, [nxrecomp](https://github.com/drakolordx7/nxrecomp), which is included here as the `base` submodule.

## Status

Early. The game runs from the title screen into the first level (the Frigate Orpheon): opening cutscene, landing, the hangar with its HUD. There are many visual bugs, and it is not playable from start to finish yet. [KNOWN_ISSUES.md](KNOWN_ISSUES.md) lists what we know is broken. Expect crashes, and please report them (see [Reporting problems](#reporting-problems)).

## PC features

| Feature | State |
|---|---|
| Any resolution and aspect ratio, ultrawide included, with a correct HUD | Working |
| FOV, anisotropic filtering, LOD bias, bloom and chromatic aberration toggles | Working |
| Window, borderless fullscreen (Alt+Enter), vsync and frame cap options | Working |
| High refresh rates (120, 144, 240 Hz and uncapped) with game speed and physics unchanged | Working in menus and cutscenes. Not yet checked in gameplay. |
| Keyboard and mouse controls with rebinding (`controls.ini` and the F1 settings page), raw mouse aim | Implemented. Mouse aim and the Switch button layout are not yet checked in gameplay. Morph ball mouse camera and free look are missing. |
| Controllers with gyro and rumble | Implemented, not yet checked in gameplay |
| HDR | In progress |
| FSR 3.1 upscaling and frame generation, DLSS or XeSS if you supply the DLLs, Reflex and Anti-Lag 2 | In progress |

## What you need

- Windows 10 or 11, 64-bit.
- A graphics card and driver with Vulkan 1.3.
- About 13 GB of free disk space.
- Your own dump of Metroid Prime Remastered, version 1.0.0 (title id `010012101468C000`), as an `.nsp`, `.xci`, `.nsz` or `.xcz` file. Updates and patches are not supported.
- Your Switch keys (`prod.keys`), dumped from your own console. If the dump was bought on another console, its `title.keys` goes next to `prod.keys`.

We do not provide dumps or keys and cannot help you get them.

## Install a release

1. Download the latest zip from the Releases page and unpack it.
2. Run `mpr_setup.exe`. Pick your dump (or drag it into the window), check that the line under it turns green, point it at your keys if it did not find them, and press Start setup. It takes about 5 minutes on a 16-core PC. You can stop it and run it again later; it carries on where it left off.
3. Start `mpr.exe` from the same folder.

The release's own `README.txt` lists the default controls and the settings you can change. `tools/setup/README.md` in nxrecomp covers the setup tool in more detail, including its command-line options and error messages.

## Build from source

You only need this to work on the code. A release is easier if you just want to play.

### Prerequisites

| Tool | Notes |
|---|---|
| Visual Studio Build Tools 2026 | C++ workload and a Windows SDK, in the default install path. The scripts call `vcvars64.bat` from there. |
| LLVM with clang-cl | Installed in `C:\Program Files\LLVM`. We use LLVM 23. |
| CMake and Ninja | CMake 4.x. Both must be on `PATH`. |
| sccache | The build scripts use it as the compiler launcher. |
| Vulkan SDK | For `spirv-val` and the validation layer. |
| Python 3.13 and [uv](https://docs.astral.sh/uv/) | For the recompiler and the test tools. |
| .NET 10 SDK | For the shader translator. |
| Git | Clone with submodules. |

`pwsh .weaver\check-toolchain.ps1` checks that each tool runs. It also checks some optional analysis tools (IDA, hactool, RenderDoc and others). Those can fail without affecting the build.

### Steps

Run these from the repository root, in `cmd` or PowerShell. Git Bash does not work because its `tar` cannot unpack the downloads.

1. Clone with the submodule.

   ```
   git clone --recurse-submodules https://github.com/drakolordx7/MetroidPrimeRemasteredRecomp
   ```

2. The scripts expect `recomp`, `runtime` and `tools` at the top level, but they arrive inside `base`. Link them (in `cmd`; no admin rights needed). These names are already in `.gitignore`.

   ```
   mklink /J recomp base\recomp
   mklink /J runtime base\runtime
   mklink /J tools base\tools
   ```

3. Create the Python environment.

   ```
   uv venv tools\.venv --python 3.13
   uv pip install --python tools\.venv -r recomp\requirements.txt
   uv pip install --python tools\.venv numpy pillow
   ```

4. Build the setup tool and extract your dump into `game\`. This writes `game\exefs`, `game\romfs` and the converted texture cache.

   ```
   pwsh -File tools\textures\scripts\fetch_third_party.ps1
   pwsh -File tools\setup\scripts\fetch_zstd.ps1
   pwsh -File tools\setup\scripts\build.ps1
   tools\setup\build\release\bin\mpr_setup_cli --input "path\to\Metroid Prime Remastered.nsp" --out game
   ```

   Add `--keys path\to\prod.keys` if it cannot find your keys. Run `mpr_setup_cli --check` with `--input` to inspect a dump without writing anything.

5. Translate the game's code to C++ and build it into libraries. The first run takes a long time. Later runs only rebuild what changed.

   ```
   recomp\scripts\build_mpr.cmd
   ```

   The script starts its own sccache server on port 24339 with the cache in `work\build\sccache`, so every checkout on the same PC shares it. Set `SCCACHE_SERVER_PORT` and `SCCACHE_DIR` first if you want a separate cache.

6. Build the texture decoder DLLs and then `mpr.exe`.

   ```
   pwsh -File tools\textures\scripts\build.ps1
   pwsh game-build\scripts\build.ps1
   ```

   The program ends up in `game-build\build\release\mpr.exe`. The first configure downloads SDL3 and a few small libraries, so it needs an internet connection. `mpr.exe` and the setup tools use the static Visual C++ runtime, so a PC that only runs them needs no redistributable.

The game also needs its translated shaders (`shader_cache`). A release ships them as a prebuilt pack that the setup tool unpacks. To build the cache yourself, see `tools/shaders/README.md` and `runtime/docs/S4d.md` in nxrecomp.

## Run and test

Run the game in a window from the repository root:

```
game-build\build\release\mpr.exe --game game
```

Developer commands, all through the project's Python environment:

```
tools\.venv\Scripts\python tools\boot\boot.py                          # rebuild, run headless for 40 s, print a summary and the log tail
tools\.venv\Scripts\python tools\boot\boot.py --env NXRT_BOOT_GFX=window
tools\.venv\Scripts\python tools\test\run_suite.py tools\test\suites\boot.toml
```

`boot.py` has more options (`--help`). The suite runs scripted, deterministic runs of the game and prints one PASS or FAIL line per run. Unit tests and the recompiler's oracle checks are described in [CONTRIBUTING.md](CONTRIBUTING.md).

## Screenshots

Screenshots will go in `docs/images/`.

<!-- Maintainer: this folder is intentionally empty. Game frames are copyrighted, so decide whether to commit any before adding them, then link them here. -->

## Reporting problems

Use the issue forms: bug report, crash report, visual glitch and feature request. Include `mpr.log` and your GPU and driver version. A screenshot of a bug in a running build is fine to attach. Never attach game files, keys or dumps. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to turn on more detailed logging.

## Contributing

Pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first. Security problems go through [SECURITY.md](SECURITY.md).

## Layout

| Path | What is in it |
|---|---|
| `base/` | The nxrecomp submodule: recompiler (`recomp`), runtime (`runtime`) and tools (`tools`) |
| `game-build/` | The CMake project that links the runtime and the translated game into `mpr.exe` |
| `docs/` | The original plan (`PLAN.md`) and reverse-engineering notes (`mpr/`) |
| `.weaver/` | Helper scripts, the tool index (`INDEX.md`), the current status (`STATUS.md`) and a changelog |

## Licence

GPL-3.0. See `LICENSE`. Third-party code keeps its own licence; the notices are in nxrecomp.
