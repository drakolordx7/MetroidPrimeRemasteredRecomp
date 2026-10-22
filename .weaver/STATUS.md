# Status: Metroid Prime Remastered PC recomp

## Done
- Toolkit (`.weaver\check-toolchain.ps1`), guard hook, Eden reference emulator, 010 Editor, Superluminal.
- Recompiler (`recomp/`): difftest 565,061/565,061, mutation 22/22, e2e 30/30, hooks; oracles locked. Lifts and compiles main/sdk/subsdk0/rtld (138,502 functions) in about 2 minutes.
- Offline graphics tools (`tools/`): shader harness, ASTC→BC7, tiling; oracles locked.
- Runtime main: ABI 3, C++ exceptions, graphics shell, Horizon services (fs/RomFS, saves, am, acc, set, time, hid, pl, audren, vi, nvdrv and stubs), NVN on Vulkan (513/523 entry points, all 204 the game uses), shader cache (67,506 blocks, 0 failures). 122/122 tests.
- Knowledge base (`docs/mpr/`), asset survey (`docs/mpr/survey/SURVEY.md`).
- Boot: the real game reaches the full title screen (logo and background movie) and main menu through our NVN-on-Vulkan backend at about 136 fps headless, and with scripted input the loading screen, where the Vulkan device is lost (~58 s). Screenshot: work\run\shot_0.png.
- Setup tool (`tools/setup`): NSP/XCI/NSZ + keys, version check, byte-identical extraction, resumable BC7 cache; 160 s full setup at quality 3, 660 s at quality 5; 13/13 unit tests, 7/7 refusals.
- High refresh: the game steps by measured frame time (`[time] mode = real`, 60 Hz lock option); movies and the front end run at real speed at 60/120/144/240 (retail ran 2-4x fast). Variable timestep chosen; physics probe ready for gameplay.
- Movies and audio: movie:: on Media Foundation (25/25 movies bit-identical to ffmpeg, title background now plays), audio paced by the sink queue, DSP-ADPCM verified on real data. Live XAudio2 playback not heard yet (no output device in the agent session).
- Play mode: window by default (Alt+Enter fullscreen, vsync option), controllers with gyro and rumble, keyboard/mouse bindings (controls.ini), mouse aim through ProcessInput, F1 settings page. Aim gating and Switch layout are unverified until gameplay is reachable.
- Test tooling: deterministic mode with per-frame state hash, input record/replay, script runner and probes, image/trace/regression comparators, Eden reference captures (work/eden_ref/ref). main is lifted with entry hooks (recomp\games\mpr\main.sites).
- GitHub: both repos humanized and published (private).

## Running
- NVN correctness to gameplay (branch `nvn2`): struct-size audit, validation clean, fix the device loss, title background, past loading into gameplay.
- Display options and frame-time performance (branch `display`): profile title stalls, pipeline prewarm, resolution, aspect/Hor+, FOV, AF, dynamic resolution off.
- Texture quality fix and release packaging (tools/textures, tools/setup, tools/release).

## Next (in this order)
0. After display merges: Extras (HDR via NTonemap, FSR 3.1 on the internal-resolution path, DLSS/XeSS DLLs, Reflex/Anti-Lag 2).
1. NVN gaps: sparse textures (MapVirtual), transform feedback, occlusion queries, pipeline prewarm.

## Shortcomings to fix
- High refresh unverified in gameplay: in-air friction fix, render-timing hook, streaming hooks, walk/jump/turn probe; morph-ball friction, projectile range and HUD timer need probe reads.
- Mouse aim, context detection, Switch button layout and beam/visor combos need checking in real gameplay; morph-ball mouse camera and free look not done; aim steps at the game tick rate above 60 fps until a late-sample camera hook exists.
- Game threads are pinned to three host cores with Windows wake-up boost off (console core model). Under heavy background load each contended mutex hand-over waits a scheduler quantum (debug 180, fixed in tests by raising priority). Decide how mpr.exe itself avoids stutter on busy PCs: raise its priority class, or relax the pinning or boost once gameplay timing is measured.
- BC7 quality: real textures go down to 28-29 dB on a few files (mean 49-50 dB); find which textures (normal maps, alpha?) and fix the encoding rather than relax the floor.
- Release launcher must run from the game folder with --exefs exefs --ini mpr.ini (the exe's default game/exefs doesn't match the setup layout).
- gfx_nvn_scene_stress failed once under load, passed alone; watch it.

## Open items
- Superluminal licence activation for its llm/mcp modes (browser step).
- `.weaver/INDEX.md` needs a plain-language pass once its pending edits are committed.

## Decisions that matter
GPL-3.0; recompile main+sdk+subsdk0 with HLE at SVC/IPC plus hook overrides (movie→Media Foundation, GetNpadState, fs as folder); Ryujinx shader translator, SPIR-V shipped; ASTC→BC7 at setup; Vulkan 1.3; prebuilt exe release, player supplies dump; Windows x64 only; repos private until release; AI tooling files (CLAUDE.md, .claude, brief preamble) stay local.
