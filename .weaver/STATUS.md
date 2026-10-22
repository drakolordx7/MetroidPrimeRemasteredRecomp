# Status: Metroid Prime Remastered PC recomp

## Done
- Toolkit (`.weaver\check-toolchain.ps1`), Eden reference emulator, 010 Editor, Superluminal.
- Recompiler (`recomp/`): difftest 565,061/565,061, mutation 22/22, e2e 30/30, hooks; oracles locked. Lifts and compiles main/sdk/subsdk0/rtld (138,502 functions) in about 2 minutes.
- Offline graphics tools (`tools/`): shader harness, ASTC→BC7, tiling; oracles locked.
- Runtime main: ABI 3, C++ exceptions, graphics shell, Horizon services (fs/RomFS, saves, am, acc, set, time, hid, pl, audren, vi, nvdrv and stubs), NVN on Vulkan (513/523 entry points, all 204 the game uses), shader cache (67,506 blocks, 0 failures). 122/122 tests.
- Knowledge base (`docs/mpr/`), asset survey (`docs/mpr/survey/SURVEY.md`).
- Gameplay: the real game plays from the title through New Game into the Frigate Orpheon (opening cutscene, landing, hangar with HUD, lighting, fog, bloom), zero Vulkan validation errors, no device loss over 7-minute runs. Known visual bugs: noise rectangle on the hangar door, dark gunship, black spike artefact.
- Setup tool (`tools/setup`): NSP/XCI/NSZ + keys, version check, byte-identical extraction, resumable BC7 cache; 160 s full setup at quality 3, 660 s at quality 5; 13/13 unit tests, 7/7 refusals.
- Display and performance: title holds 140 fps at a 144 cap (was 33), ~220 uncapped; fixes: per-page heap map table, high priority class when playing, pipeline cache saved, background pool import; pipeline prewarm; any resolution, Hor+ ultrawide with HUD proportions, dynamic resolution off, FOV, AF, LOD bias, bloom/chromatic aberration toggles.
- Texture quality: normal maps fixed (min 17.4 to 33.6 dB, 4,413/4,413 pass floors); setup 295 s at default. Release: builder with game-data refusal, 286 MiB zip incl. shader pack, mpr.exe finds its game folder; clean-room install reaches the title.
- High refresh: the game steps by measured frame time (`[time] mode = real`, 60 Hz lock option); movies and the front end run at real speed at 60/120/144/240 (retail ran 2-4x fast). Variable timestep chosen; physics probe ready for gameplay.
- Movies and audio: movie:: on Media Foundation (25/25 movies bit-identical to ffmpeg, title background now plays), audio paced by the sink queue, DSP-ADPCM verified on real data. Live XAudio2 playback not heard yet (no output device on the test machine).
- Play mode: window by default (Alt+Enter fullscreen, vsync option), controllers with gyro and rumble, keyboard/mouse bindings (controls.ini), mouse aim through ProcessInput, F1 settings page. Aim gating and Switch layout are unverified until gameplay is reachable.
- Test tooling: deterministic mode with per-frame state hash, input record/replay, script runner and probes, image/trace/regression comparators, Eden reference captures (work/eden_ref/ref). main is lifted with entry hooks (recomp\games\mpr\main.sites).
- GitHub: both repos are set up and private until release.

## Running
- NVN correctness to gameplay (branch `nvn2`): struct-size audit, validation clean, fix the device loss, title background, past loading into gameplay.
- Rendering fidelity in gameplay vs Eden references (branch `nvn3`).
- Gameplay verification of PC features: probes, physics at 60-240 Hz, controls and mouse aim, morph-ball camera, core-model stutter (branch `verify`).
- Extras: HDR, FSR 3.1, DLSS/XeSS (user DLLs), Reflex/Anti-Lag 2 (branch `extras`).
- Full-game stability sweep: warp tour of every area, save/load, menus, visors, cinematics; SWEEP.md (branch `sweep`).

## Next (in this order)
0. Gameplay performance: stutter and low fps in gameplay (user observed), profile in-world frames, shader/pipeline misses, streaming, CPU vs GPU.
1. NVN gaps: sparse textures (MapVirtual), transform feedback, occlusion queries, pipeline prewarm.

## Shortcomings to fix
- High refresh unverified in gameplay: in-air friction fix, render-timing hook, streaming hooks, walk/jump/turn probe; morph-ball friction, projectile range and HUD timer need probe reads.
- Mouse aim, context detection, Switch button layout and beam/visor combos need checking in real gameplay; morph-ball mouse camera and free look not done; aim steps at the game tick rate above 60 fps until a late-sample camera hook exists.
- Release: hardcoded dev shader path in nvn_shaders.cpp, RGBA8/BC5 cache entries (with S4f); licence texts still missing for Eden/yuzu GPL-2.0, libc++abi, MSVC runtime.
- gfx_nvn_scene_stress failed once under load, passed alone; watch it.

## Open items
- README build-from-source uses junctions (baseecomp etc.); verify on a fresh clone, or make the scripts find base/ directly.
- Add screenshots to docs/images (maintainer's choice).
- README screenshots: the maintainer adds real captures to `docs/images/` (none are committed).

## Decisions that matter
GPL-3.0; recompile main+sdk+subsdk0 with HLE at SVC/IPC plus hook overrides (movie→Media Foundation, GetNpadState, fs as folder); Ryujinx shader translator, SPIR-V shipped; ASTC→BC7 at setup; Vulkan 1.3; prebuilt exe release, player supplies dump; Windows x64 only; repos private until release.
