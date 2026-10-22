# Metroid Prime Remastered PC recomp: plan v2

## Context
Native Windows x64 build of Metroid Prime Remastered (Switch, 010012101468C000, v1.0.0, build ID 67C9CA14…). Must-haves: arbitrary resolution/ultrawide, 120 fps and beyond, raw mouse aim, full KB+M. Optional: upscaling, frame gen. GPL-3.0, public GitHub, prebuilt exe, player brings their own dump. Phase 0 (toolkit) is done. A read-only study of 18 reference projects closed most of the open questions.

## What the study settled
- Symbols confirmed. `main` exports C++ mangled names; mods hook `CPlayerMP1::ProcessInput`, `CStateManagerGameLogicMP1::GameMainLoop(…, float dt)`, `CFirstPersonCameraMP1::Think`, `NTonemap::build_tonemap_eval_params` etc. by name. MetroidPrimePort lists ~150 "Remastered 1.0.0" addresses. Image base 0x7100000000.
- Known layouts: CPlayerMP1 (+0x5cc pitch, +0x9d0 morph ball), CTweakPlayerMP1 (+0x138 max pitch), CGameCameraMP1 (+0x25c FOV), CFinalInput (0x398, 0x38 controls), CPlayerStateMP1 power-ups, CGameState play time. Input enters via `nn::hid::GetNpadStates`.
- Assets: all RFRM. TXTR = BCn/BC7/ASTC, Tegra block-linear. Shaders sit inside MTRL MaterialArchives (blob type unverified, likely Maxwell). Movies = H.264 MP4 in FMV0. HUD = GUIF frames; menus likely Scaleform (GFXL). Audio codec unknown.
- Nobody has solved: mouse aim, >60 fps, HDR, ASTC→BC7 offline, zero-play pipeline prewarm, MPR shader container extraction. These are our original work.

## Phase 2 gate results (measured on the v1.0.0 dump)
- NSP → program NCA e66e21cd…, key generation 11, SDK 12.3.1. ExeFS: main 15.8 MB, sdk 5.8 MB, subsdk0 3.4 MB, rtld, main.npdm.
- main build ID 67C9CA1428222752F951021464A7B3597EB98FEC = v1.0.0 confirmed. sdk 2217A4A3…, subsdk0 1506DE55….
- Symbols: main dynsym 103,010 entries, 92,784 named functions defined; imports 422 (317 `nn::`, 41 `movie::`, 4 `nv`, `nvnBootstrapLoader`, libc). sdk 26,890 defined / 13 imports; subsdk0 = Nintendo multimedia (movie::/stagefright, mkv, FDK-AAC, opus) 10,896 defined / 657 imports.
- Lifter coverage: 100% of instruction words: main 4,237,540, sdk 1,457,244, subsdk0 851,512.
- FPCR: never written by main or subsdk0; 3 `msr fpcr` in sdk only → the lifter's FPCR gap is irrelevant to game code. 76 `svc` sites, all in sdk.
- OS-layer decision: recompile main + sdk + subsdk0 entirely; HLE at the 76 SVC sites + IPC services (Wonder style, SDK-version-robust), with targeted hook-table overrides where a host path is better: `movie::` → Media Foundation (smo `nnmovie_mf.c`, same multimedia stack), `nn::hid::GetNpadStates*` for input injection, fs as a RomFS folder.
- Asset survey (`docs/mpr/survey/SURVEY.md`): 67,506 distinct NVN shader blocks (583 sets in MaterialArchive.arc + 46,936 in pak MTRLs). Translator: Ryujinx (9,164/9,164 spirv-val on a seeded sample vs smo 41%). Watch: `PIXLD.MY_INDEX` in ~97% of pixel shaders (likely driver alpha-to-coverage dither, needs runtime c[0] data); 38% need the retry mode → ship translated SPIR-V. Textures: 6,927 (4,369 ASTC 5x4/5x5/8x5, 4,350 MPix; 2,368 BCn passthrough; 45 colour LUTs 33³); untiling verified against real buffers; ASTC→BC7 about 12-23 min one-time in-process (PSNR mean 54.6 dB). Audio: all DSP-ADPCM through `nn::audio` AudioRenderer via Retro's CAxal engine, no middleware. Movies: 25 × H.264 Main 1600×900 60 fps (7 with AAC 5.1), Media Foundation decodes all at 91-128 fps. UI: 14 GUIF frames, no Scaleform; the front end is a 3D scene. Timestep: `CGameArchitectureSupport::Update` hard-codes 1/60 per rendered frame.

## Architecture (decisions)
- CPU / lifter: fork smo-recomp's lifter (Python, `.eh_frame`-exact discovery, Unicorn difftest with mutation testing, `fpexact.h`). Add Wonder's newer-SDK instruction coverage (LSE atomics, LDXP/STXP, crypto, scalar SIMD) and jump-table resolver; ssbu's C++ exception lifting (`recomp_eh.py`), site re-lift + hook table + inline check; ScarletNX's separate TPIDRRO and its a64 audit corpus as a stricter oracle.
- OS layer: decided at the Phase 1 gate by measurement. Default: Wonder style. Recompile the whole `sdk` and answer at SVC/IPC level (robust across SDK versions; MPR is a 2023 SDK, much newer than SMO's 7.3.2). Fallback: smo's nn:: import replacement where hot (fs, hid, allocator, threads). Gate inputs: SDK version string, import count, NVN version.
- Runtime core from smo: identity map at 0x7100000000 (guest ptr = host ptr), pagefile-backed heap that NVN pools truly alias, Win32 thread per guest thread with the 3-core pinning model (free scheduling failed 4/6 boots in SMO).
- Graphics: NVN at `nvnBootstrapLoader` → Vulkan 1.3. Base on smo's `nvn_vk` backend (pipeline libraries, push descriptors, stream ring, watchdog); use Wonder's NVN docs/DEBUG logs as the checklist (iGPU selection, NVIDIA ASTC driver crash, barriers, synchronous submit). Shaders: Ryujinx translator offline (Wonder harness) vs smo's translator. Run both on MPR's shaders, keep the higher spirv-val pass rate. Textures: ASTC → BC7 transcoded once at setup into a cache (new work; avoids the 4-9x RGBA8 memory blowup). Pipelines: we record pipeline keys from automated room tours and ship them → zero first-run stutter.
- Movies: H.264 via Media Foundation (smo `nnmovie_mf.c`), FFmpeg fallback.
- Audio: recompiled SDK audio renderer driven by a host clock (smo), XAudio2/SDL3 out.
- Input: SDL3 3.4.x pads (hot-plug, gyro, rumble) + raw mouse via SDL3 relative mode, injected by a trampoline on `CPlayerMP1::ProcessInput` (yaw on transform, pitch at +0x5cc), buttons synthesized at the `GetNpadStates`/`CFinalInput` layer.
- High refresh: measure, then choose. Experiment first: run at dt 1/120 and 1/240 with the physics probe (theboy181's 120 fps patch reportedly kept correct physics → MPR may already be dt-clean). Few deviations → variable timestep + fixes (lowest latency). Many → 60 Hz logic + render interpolation (MetroidPrimePort's FRAME_INTERPOLATION design: camera, actor transforms, skinned poses, particles; snap on cuts/teleports). Either way, mouse look is applied every rendered frame.
- Release: prebuilt exe + translated SPIR-V + pipeline keys ship; the player's dump supplies RomFS; setup tool checks build ID and file hashes, extracts, transcodes textures. Generated C++ never committed; release built locally by a script (ssbu `make_release.py` pattern, audited manifest).

## Work areas
Seven areas, each with a code location and a pass/fail check.

| Area | Owns | Check (pass/fail) | Repeating step |
|---|---|---|---|
| S1 Recompiler | `recomp/` | Unicorn difftest + mutation test; coverage report on MPR main+sdk | next unimplemented/failing instruction shape |
| S2 Binary knowledge | `work/`, `tools/analysis` | symbol/import counts; known mod offsets resolve to the right names | extract struct/func facts per class into `docs/mpr/` |
| S3 OS/HLE | `runtime/os`, `runtime/services` | boot milestones; service-call log has no unknowns; determinism hash stable | next unhandled SVC/IPC command |
| S4 Graphics | `runtime/gfx`, `tools/shaders`, `tools/textures` | spirv-val pass rate; Vulkan validation clean; RenderDoc image asserts | next failing shader / texture format / draw |
| S5 Test tooling | `tools/test` | same input replay twice → identical state hashes | next room in the warp tour |
| S6 PC features | `runtime/pc` | physics probe 60/120/240 identical; mouse delta→angle linear; HUD layout checks | per feature |
| S7 Setup/release | `tools/setup` | fresh-machine install from a dump reaches title screen | - |

Rules: the oracle scripts are hash-locked, and a project hook (ScarletNX `guard.py` pattern) blocks edits to them and keeps game data out of git. No inline asm. Each area keeps a dev log under `docs/` and numbered bug notes (`docs/debug/NNN.md`: symptom, cause, fix).

## Phases
0. Toolkit (done).
1. Pre-dump scaffolding (now): S1 forks and merges the lifter + difftest; S5 builds input record/replay, scripted-run DSL (`@area` waits, `@goto`, warp), screenshot/state-hash/regression tools; S3 runtime skeleton (loader, memory map, threads, log/crash/freeze reports); S4 Vulkan shell + shader harness; project hooks/skills. Reference emulator: try Eden now; fallback a Ryubing build you supply.
2. Dump intake (gate): extract, nx2elf, IDA databases (main, sdk, subsdk), SDK/NVN version, import list, `recomp.py cover`, FPCR/NEON scan, shader blob identification, texture-format tally, audio codec. The OS-layer and translator decisions are made at this gate.
3. Lift + link all modules; difftest green.
4. Boot: SVC/IPC, fs/RomFS, saves, threads → first NVN call.
5. Title screen: NVN/Vulkan, untiling, BC7 cache, shaders, audio, movies.
6. Playable: warp tour of every room, scripted runs, trace/image diffs vs emulator; full playthrough Frigate → credits.
7. PC features: resolution/ultrawide/HUD; high-fps experiment then implementation; raw mouse + KB+M; settings overlay.
8. Extras: HDR, FSR 3.1 upscale + frame gen, DLSS/XeSS DLLs, Reflex/Anti-Lag 2.
9. Release: setup tool, packaging, docs.

## PC feature spec (Phases 7 and 8)
- Mouse: radians-per-count sensitivity (Source-scale display), separate vertical, pitch limit from tweak, no smoothing/accel, applied per rendered frame and sampled late (just before camera update). Free aim when not locked; lock-on hands camera to target and re-syncs after. Separate sensitivity for morph-ball camera and scan/map. Pointer locked in game, released in menus; mouse support in menus/map (drag rotate, wheel zoom) where the UI allows.
- Bindings (MetroidPrimePort defaults): WASD (strafe), LMB fire/charge, RMB lock-on, MMB/F missile, Space jump, Ctrl/C morph, Q alt lock-on, Alt free look, Tab/M map, 1-4 beams, 5-8 visors, wheel cycles beams; contexts gameplay/morph/map/menu/scan with tap/hold/double-tap/toggle; rebinding file + in-game UI. Controllers and gyro keep working.
- Display: any resolution, aspect 16:9 to 32:9 with correct HUD (GUIF scaled, Scaleform menus pillarboxed), FOV slider, dynamic resolution off, LOD/draw distance, anisotropic filtering, shadow resolution, post-FX toggles, borderless/exclusive fullscreen, VRR, frame limiter, uncapped/120/144/240/360.
- Latency: late input sampling, limiter waits before input poll, optional NVIDIA Reflex (VK_NV_low_latency2) / AMD Anti-Lag 2.
- HDR: replace the game's tonemap output (`NTonemap`, per-room params) with an HDR10/scRGB path.
- Upscale/frame gen: FSR 3.1 built-in (Vulkan), DLSS/XeSS from user DLLs.
- Free extras: loose-file mod folder over RomFS, Switch save import (same `CGameState` stream), skip boot logos, dev menu (warp, IGT, noclip) behind a flag.
- Targets on your RTX 3080: 4K ≥120 fps, 1440p ≥240 fps, no shader-compile stutter.

## Verification
- Lifter: difftest + mutation suite each batch; coverage 100% of MPR instruction shapes.
- Runtime: boot milestones; deterministic replay → identical per-frame state hashes on two runs.
- Gameplay: warp tour reaches every room without crash/glitch flag; scripted runs hit checkpoints; trace/image diffs vs reference emulator.
- Graphics: spirv-val 100%; Vulkan validation clean; RenderDoc asserts on key frames.
- High fps: physics probe (walk speed, jump height, morph friction, projectile range, timers) identical at 60/120/240.
- Mouse: logged raw deltas vs applied yaw/pitch are linear, unsmoothed, same at every fps.
- Performance: frame-time logs at the targets above.
- Screenshots at first boot, title screen, first gameplay and each feature batch.

## Risks
SDK/NVN version gap vs reference runtimes; shader blob format unverified; NEON/FPCR coverage; 3-core timing; build size (~1+ GB C++, ~45 min builds); reference emulator availability.
