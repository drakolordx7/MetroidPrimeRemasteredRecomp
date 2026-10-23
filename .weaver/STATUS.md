# Status: Metroid Prime Remastered PC recomp

## Where it stands
The real game runs natively on Windows from the title screen through New Game into the Frigate Orpheon (opening cutscene, landing, hangar with HUD, lighting, fog, bloom, audio, movies). Both GitHub repos are public: github.com/drakolordx7/MetroidPrimeRemasteredRecomp and github.com/drakolordx7/nxrecomp.

## Done (merged on main)
- Recompiler (`recomp/`): difftest 565,061/565,061, mutation 22/22, e2e 30/30, hooks; oracles locked. Lifts and compiles main/sdk/subsdk0/rtld (138,502 functions) in about 2 minutes. Hook sites in `recomp/games/mpr/main.sites`.
- Offline tools (`tools/`): shader harness (Ryujinx), ASTC→BC7 (normal maps fixed, 4,413/4,413 pass), tiling, setup tool (NSP/XCI/NSZ + keys, version check, ~5 min setup), release builder (refuses game data, 286 MiB zip, clean-room install reaches the title), test tooling (deterministic mode, state hash, input replay, script runner, probes, comparators, Eden references).
- Runtime (`runtime/` main): ABI 3, C++ exceptions, Horizon services, NVN on Vulkan (struct sizes from the game, storage images, sparse textures, occlusion, transform feedback), shader cache (67,506 blocks), movies on Media Foundation, audio paced by the sink, window + controllers + keyboard/mouse bindings + mouse aim + F1 settings, real-time timestep (60/120/144/240 run at real speed), display options (resolution, Hor+ ultrawide, FOV, AF, LOD bias, post toggles, dynamic resolution off), perf fixes (title 140 fps at a 144 cap), pipeline prewarm, HDR10/scRGB, Reflex, frames-ahead pacing, FSR 1, scene scale. S18: frame limiter moved to the frame boundary (input to present 49 → 9 ms p50 at a 60 cap), pool imports through small heap views (63 → 0.19 ms each), unlinked programs no longer rebuilt every bind. S19: button prompts fixed (small-texture block height) with Switch/Xbox/PlayStation/keyboard styles switchable live, setup tool writes BC5/RGBA8 entries (encoder rev 3, 4,369 entries in 3.5 min), null-image barrier and image-layout validation errors fixed, shader pack 13,020 entries, release licences added. Gameplay runs need `NXRT_NVN_SHADER_CACHE=D:\AI\Active\Metroid-Prime\work\shader_cache\spirv`.

## Running (overnight)
- Last merge batch (perf2 + polish into runtime main): 152/152 tests, gameplay boot 170 s, 9,057 presents, 0 failed textures.
- S21 `stutter`: async texture prepare at area loads, movie decoder off the main thread, Reflex vs new pacing, vsync/uncapped matrix.
- S20 `stab`: sweep hangs, boot deadlocks, frigate_air_lock crash, warp stalls, lifter `wfe` yield, finish the sweep.
- S4g `nvn4`: colour-noise rectangles (18 areas + hangar door), misaligned engine jets, black textures, magmoor_workstation graphics crash.

## Full-game sweep (docs/mpr/SWEEP.md)
184 of 275 areas reached: 159 OK, 18 visual issues (colour-noise rectangles, worst in tallon_biohazard_containment, chozo_watery_hall_access, chozo_totem_access), 2 crashes (frigate_air_lock particle state on the loader thread, magmoor_workstation BoxInFrustumPlanes), 4 post-warp hangs in CGraphicsFrameToken::WaitUntilFinished and 2 boot deadlocks in CScopedSceneTransferLock (lost wake-up suspected; the watchdog now dumps kernel waiters). Fixed: loading freezes from the spin-only LockBusyMutex (host replacement; lifter idea: make `wfe` yield). Not visited: rest of Phendrana, Phazon Mines, Impact Crater. Rerun: `tools/.venv/Scripts/python tools/test/sweep.py --exe game-build/build/release/mpr.exe --jobs 2 --resume`.

## Next (queue, in order)
1. Release fixes: link mpr.exe, setup tools and astcdec statically (`/MT`) so players don't need the VC++ redistributable (decided: static, no installer step); `gfx_nvn_scene_texture` depends on an old bc7_cache entry (make the test generate its own reference); fix the mangled backslash lines in INDEX.md (polish entry).
2. Gameplay physics table at 60/120/144/240 (walk at 120 looked 4% slow; jump reading suspicious), keyboard beam/visor keys in game.
3. Humanizer pass over the S8-S19 dev docs, then publish.
4. Later: FSR 3.1/DLSS/XeSS need motion vectors (S14.md); HDR on a real HDR display; AMD Anti-Lag 2.

## Shortcomings to fix
- High refresh and mouse aim still need gameplay verification (S13).
- README build-from-source uses junctions (base\recomp etc.); verify on a fresh clone or make the scripts find base/ directly.
- Timing-sensitive tests (kernel_threads, svc_info, gfx_nvn_scene_stress, watchdog) can fail under heavy machine load and pass alone; gfx_nvn_scene_texture depends on the bc7_cache contents in its build folder.
- New dev docs (S8-S18) have not had the plain-language pass yet.

## Decisions that matter
GPL-3.0; recompile main+sdk+subsdk0 with HLE at SVC/IPC plus hook overrides (movie→Media Foundation, GetNpadState, fs as folder); Ryujinx shader translator, SPIR-V shipped; ASTC→BC7 at setup; Vulkan 1.3; variable timestep; prebuilt exe release, player supplies dump; Windows x64 only; repos public; local tooling files stay out of the published history (publish.ps1 scrubs them).
