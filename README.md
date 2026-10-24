# Metroid Prime Remastered for Windows (unofficial PC port)

A native Windows port of Metroid Prime Remastered, made by recompiling the Nintendo Switch release (version 1.0.0) into a normal Windows program. It is not an emulator. The game's code is translated to C++ ahead of time, a runtime stands in for the Switch's system services, and the game's graphics API (NVN) runs on Vulkan. It has a launcher, a setup tool, mouse and keyboard controls, any resolution and aspect ratio, and high refresh rates.

[Download the latest release](https://github.com/drakolordx7/MetroidPrimeRemasteredRecomp/releases/latest)

The release has no game files. You need your own dump of Metroid Prime Remastered version 1.0.0 and the keys from your own Switch. Not affiliated with Nintendo or Retro Studios.

## Requirements

- Windows 10 (1903 or later) or Windows 11, 64-bit
- A GPU and driver with Vulkan 1.3. It has been tested on an NVIDIA GeForce RTX 3080 only; AMD and Intel GPUs are untested
- About 14 GB of free disk space
- Your dump of the game, version 1.0.0 (`.nsp`, `.xci`, `.nsz` or `.xcz`; updates and patches are not supported) and your `prod.keys` (if the dump was bought on another console, also its `title.keys`, next to `prod.keys`)

## Usage

1. Unzip the release into a folder with a short path (under about 180 characters) and run `mpr_launcher.exe`.
2. Press "Set up game files...", choose your dump and your `prod.keys`, and press Start setup. It takes about 5 minutes on a 16-core PC, longer on fewer cores. You can stop it and run it again later.
3. When setup closes, the launcher prepares shaders for your GPU (a few minutes, once per driver). When it says "Ready to play.", press Play.

Settings are in the launcher (display, mouse, keyboard, controller, button icons) and on the F1 page in the game, and are saved to `controls.ini` in the game folder. Saves are in `%APPDATA%\MPRRecomp\save`. Logs (`mpr.log`, `setup.log`) are in the game folder. To update, unzip a new release over the old folder. To uninstall, delete the folder and the save folder.

Defaults: WASD move, mouse aims, left button fires, right button or Q locks on, middle button or F fires missiles, Space jumps, Ctrl or C is the morph ball, Tab or M opens the map, Escape pauses, 1 to 4 pick the beam and 5 to 8 the visor. Xbox, PlayStation and Switch controllers work. Alt+Enter toggles fullscreen and F2 shows the frame rate. `HELP.txt` in the release lists every key, every setting and the fixes for common problems.

## Reporting problems

[Open an issue](https://github.com/drakolordx7/MetroidPrimeRemasteredRecomp/issues/new/choose) and attach `mpr.log` from the run where it happened (the next run keeps the old one as `mpr.log.prev`). The top right of the launcher and the "mpr 0.1.0" line near the top of the log show your version. For a crash, also attach `mpr_crash.txt` or `mpr_fatal.txt`. Never attach game files, your dump or your keys.

## Contributing

- Open pull requests against `main`. Say what you changed and what you ran. Keep unrelated clean-ups out, and write commit subjects as one plain sentence.
- Code in `recomp/`, `runtime/` and `tools/` lives in [nxrecomp](https://github.com/drakolordx7/nxrecomp), included here as the `base` submodule. Game bugs, `game-build/` and the docs belong here.
- Never put game data, keys or anything extracted from the game in a pull request.
- Build (Visual Studio Build Tools with the C++ workload, LLVM 23 with clang-cl, CMake, Ninja, sccache, Vulkan SDK, Python 3.13 with uv, .NET 10; run from `cmd` or PowerShell, not Git Bash):

```
git clone --recurse-submodules https://github.com/drakolordx7/MetroidPrimeRemasteredRecomp
mklink /J recomp base\recomp
mklink /J runtime base\runtime
mklink /J tools base\tools
uv venv tools\.venv --python 3.13
uv pip install --python tools\.venv -r recomp\requirements.txt numpy pillow
pwsh -File tools\textures\scripts\fetch_third_party.ps1
pwsh -File tools\setup\scripts\fetch_zstd.ps1
pwsh -File tools\setup\scripts\build.ps1
tools\setup\build\release\bin\mpr_setup_cli --input "Metroid Prime Remastered.nsp" --out game
recomp\scripts\build_mpr.cmd
pwsh -File tools\textures\scripts\build.ps1
pwsh game-build\scripts\build.ps1
```

`build_mpr.cmd` lifts the game's code and takes a while the first time. The program ends up in `game-build\build\release\mpr.exe`. Add `-Release -Version 0.1.0` to the last command for the package build that `tools\release\make_release.py` zips. The tests are `pwsh runtime\scripts\build.ps1 -Test` (runtime) and `pwsh -File tools\setup\scripts\build.ps1 -Test` (setup tool). Folders with an `oracle\LOCKED` file are checks that must not be edited. More detail is in the READMEs of each folder in nxrecomp.

## Credits

Maintained by [drakolordx7](https://github.com/drakolordx7).

Built on the work of others:

- Recompiler and runtime design: [smo-recomp](https://github.com/Coz-0/smo-recomp) (the lifter this one started from), [SuperMarioWonderRecomp](https://github.com/BelmanteGu) by Projeto Belmante, [ssbu-recomp](https://github.com/OpenSmash-Ultimate/ssbu-recomp) (C++ exceptions), [ScarletNX](https://github.com/scarletnx/ScarletNX) (service layouts) and [LASRecomp](https://github.com/peiikai/LASRecomp)
- [Ryujinx](https://ryujinx.app) (Ryubing): the Maxwell shader translator and the audio renderer port
- [Eden](https://eden-emu.dev) and yuzu: file system, audio and display service layouts, and Eden as the reference for checking frames
- [retrotool](https://github.com/PrimeDecomp/retrotool) and [PrimeRemasterStructs](https://github.com/PrimeDecomp/PrimeRemasterStructs) by PrimeDecomp: Metroid Prime Remastered file formats
- Libraries: [SDL3](https://github.com/libsdl-org/SDL), [Dear ImGui](https://github.com/ocornut/imgui), [volk](https://github.com/zeux/volk), [Vulkan Memory Allocator](https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator), [Vulkan-Headers](https://github.com/KhronosGroup/Vulkan-Headers), [astc-encoder](https://github.com/ARM-software/astc-encoder), [bc7enc_rdo](https://github.com/richgel999/bc7enc_rdo), [zstd](https://github.com/facebook/zstd), AMD FidelityFX FSR 1, DejaVu Sans, and the [Kenney Input Prompts](https://kenney.nl/assets/input-prompts) icons

Contributors and testers: none yet. Everyone who sends a fix or a useful log goes here.

Licences of the third-party parts are in the `licenses` folder and `THIRD_PARTY_NOTICES.txt` of the release.

## License

GPL-3.0, see [LICENSE](LICENSE). Third-party components keep their own licenses.
