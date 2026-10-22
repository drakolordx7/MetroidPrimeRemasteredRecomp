# Status: Metroid Prime Remastered PC recomp

## Where it stands
The real game runs natively on Windows from the title screen through New Game into the Frigate Orpheon (opening cutscene, landing, hangar with HUD, lighting, fog, bloom, audio, movies). Both GitHub repos are public: github.com/drakolordx7/MetroidPrimeRemasteredRecomp and github.com/drakolordx7/nxrecomp.

## Done (merged on main)
- Recompiler (`recomp/`): difftest 565,061/565,061, mutation 22/22, e2e 30/30, hooks; oracles locked. Lifts and compiles main/sdk/subsdk0/rtld (138,502 functions) in about 2 minutes. Hook sites in `recomp/games/mpr/main.sites`.
- Offline tools (`tools/`): shader harness (Ryujinx), ASTC→BC7 (normal maps fixed, 4,413/4,413 pass), tiling, setup tool (NSP/XCI/NSZ + keys, version check, ~5 min setup), release builder (refuses game data, 286 MiB zip, clean-room install reaches the title), test tooling (deterministic mode, state hash, input replay, script runner, probes, comparators, Eden references).
- Runtime (`runtime/` main): ABI 3, C++ exceptions, Horizon services, NVN on Vulkan (struct sizes from the game, storage images, sparse textures, occlusion, transform feedback), shader cache (67,506 blocks), movies on Media Foundation, audio paced by the sink, window + controllers + keyboard/mouse bindings + mouse aim + F1 settings, real-time timestep (60/120/144/240 run at real speed), display options (resolution, Hor+ ultrawide, FOV, AF, LOD bias, post toggles, dynamic resolution off), perf fixes (title 140 fps at a 144 cap), pipeline prewarm, HDR10/scRGB, Reflex, frames-ahead pacing, FSR 1, scene scale.

## Unmerged work (resume here)
Merged into runtime main at the end of the session: nvn3 (rendering fixes so far), verify (aim, free look, ball camera, probes), sweep (warp tour suite), perf (notes only). Branch notes: runtime\docs\S4f.md, S13.md, S15.md, S18.md.
- `prompts` (runtime-wt\prompts, commit 436e77b "WIP"): NOT merged; conflicts with the extras settings code (play_config.cpp, play_types.h, test_play_config.cpp, nvn_core.h, nvn_texdata.h, nvn_texture_registry.cpp), all additive. Contains the important fix for wrongly untiled small textures (console_block_height in nvn_texture_layout.cpp: 263 textures incl. the 173 button icons) and the Switch/Xbox/PlayStation/keyboard prompt styles (Kenney Input Prompts, CC0). Merge it first next session.
- nvn3 and sweep may have a last commit after the merge: `git -C runtime log main..nvn3` / `main..sweep`.
- Open from S4f (user saw the player model and first-person arm render correctly in the latest nvn3 build): misaligned engine jets, hangar-door noise (texture-pool slot race suspected), black textures, broken character model.
- Open from S13: physics deviation table (walk at 120 vs 60 looked 4% slow, unconfirmed), keyboard beam/visor keys unverified after the pulse fix, core-model stutter numbers, guest-wait stalls during warp loads.
- Open from S18: no measurements yet; hypothesis for the 250-360 ms latency: frame limiter sleeps inside present while the game's queue fills, plus up to 4 submissions in flight. Plan in S18.md.

## Full-game sweep (docs/mpr/SWEEP.md)
184 of 275 areas reached: 159 OK, 18 visual issues (colour-noise rectangles, worst in tallon_biohazard_containment, chozo_watery_hall_access, chozo_totem_access), 2 crashes (frigate_air_lock particle state on the loader thread, magmoor_workstation BoxInFrustumPlanes), 4 post-warp hangs in CGraphicsFrameToken::WaitUntilFinished and 2 boot deadlocks in CScopedSceneTransferLock (lost wake-up suspected; the watchdog now dumps kernel waiters). Fixed: loading freezes from the spin-only LockBusyMutex (host replacement; lifter idea: make `wfe` yield). Not visited: rest of Phendrana, Phazon Mines, Impact Crater. Rerun: tools\.venv\Scripts\python tools	est\sweep.py --exe game-builduild
elease\mpr.exe --jobs 2 --resume.

## Next
1. Merge the branches above, rerun tests and boot once, publish (`pwsh .weaver\publish.ps1`; humanizer pass on new docs first).
2. Finish S18 (latency is the top issue for mouse play) and the S4f visual bugs.
3. Then: FSR 3.1/DLSS/XeSS need motion vectors (S14.md says what it takes); AMD Anti-Lag 2 untested (no AMD GPU); HDR untested on a real HDR display.

## Shortcomings to fix
- End-of-session batch: 151 tests, 1 load-sensitive failure (gfx_nvn_scene_state, passes alone) that logged a real validation error: vkCmdPipelineBarrier2 with a null image (find the caller). Gameplay boot ran 170 s; shader block 46742355274dd77e is missing from the cache.
- The setup tool must follow the new texture cache entry formats (RGBA8 / BC5, docs in runtime/docs/S4f.md).
- High refresh and mouse aim still need gameplay verification (S13).
- Licence texts missing in the release for Eden/yuzu GPL-2.0 snippets, libc++abi, MSVC runtime.
- README build-from-source uses junctions (base\recomp etc.); verify on a fresh clone or make the scripts find base/ directly.
- Timing-sensitive tests (kernel_threads, svc_info, gfx_nvn_scene_stress, watchdog) can fail under heavy machine load and pass alone; gfx_nvn_scene_texture depends on the bc7_cache contents in its build folder.
- New dev docs (S8-S18) have not had the plain-language pass yet.

## Decisions that matter
GPL-3.0; recompile main+sdk+subsdk0 with HLE at SVC/IPC plus hook overrides (movie→Media Foundation, GetNpadState, fs as folder); Ryujinx shader translator, SPIR-V shipped; ASTC→BC7 at setup; Vulkan 1.3; variable timestep; prebuilt exe release, player supplies dump; Windows x64 only; repos public; local tooling files stay out of the published history (publish.ps1 scrubs them).
