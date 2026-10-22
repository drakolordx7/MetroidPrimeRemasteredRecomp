# Status: Metroid Prime Remastered PC recomp

## Where it stands
The real game runs natively on Windows from the title screen through New Game into the Frigate Orpheon (opening cutscene, landing, hangar with HUD, lighting, fog, bloom, audio, movies). Both GitHub repos are public: github.com/drakolordx7/MetroidPrimeRemasteredRecomp and github.com/drakolordx7/nxrecomp.

## Done (merged on main)
- Recompiler (`recomp/`): difftest 565,061/565,061, mutation 22/22, e2e 30/30, hooks; oracles locked. Lifts and compiles main/sdk/subsdk0/rtld (138,502 functions) in about 2 minutes. Hook sites in `recomp/games/mpr/main.sites`.
- Offline tools (`tools/`): shader harness (Ryujinx), ASTC→BC7 (normal maps fixed, 4,413/4,413 pass), tiling, setup tool (NSP/XCI/NSZ + keys, version check, ~5 min setup), release builder (refuses game data, 286 MiB zip, clean-room install reaches the title), test tooling (deterministic mode, state hash, input replay, script runner, probes, comparators, Eden references).
- Runtime (`runtime/` main): ABI 3, C++ exceptions, Horizon services, NVN on Vulkan (struct sizes from the game, storage images, sparse textures, occlusion, transform feedback), shader cache (67,506 blocks), movies on Media Foundation, audio paced by the sink, window + controllers + keyboard/mouse bindings + mouse aim + F1 settings, real-time timestep (60/120/144/240 run at real speed), display options (resolution, Hor+ ultrawide, FOV, AF, LOD bias, post toggles, dynamic resolution off), perf fixes (title 140 fps at a 144 cap), pipeline prewarm, HDR10/scRGB, Reflex, frames-ahead pacing, FSR 1, scene scale.

## Unmerged work on branches (resume here)
Each stream's branch lives in runtime (worktrees under `runtime-wt\<branch>`), with its notes in `runtime-wt\<branch>\docs\S<n>.md`. Merge order suggestion: nvn3, verify, sweep, prompts, perf; run the runtime tests once and `tools\boot\boot.py` once after the batch.
- `nvn3` (S4f, rendering fidelity): rainbow textures fixed, cutscene gun coloured, cube-map layered rendering, no dev shader path. Open: first-person arm and gun missing/black, misaligned engine jets, hangar-door noise (likely a texture-pool slot race), black textures, broken character model, BC5/RGBA8 cache entries.
- `verify` (S13, gameplay verification): probe fixes (yaw axis, physics velocity guard, @give/@mash/@run/@sleep steps). Open: physics deviation table at 60-240, binding-by-binding run, mouse linearity log, morph-ball camera, free look.
- `sweep` (S15, full-game sweep): warp-tour suite and SWEEP.md in progress.
- `prompts` (S17): warped button icons (cause being traced: icon texture decode/UV vs font) and prompt styles Switch/Xbox/PlayStation/keyboard-mouse from a free icon pack.
- `perf` (S18): gameplay stutter/low fps and input latency (measured 250-360 ms input→present, far too high).

## Next
1. Merge the branches above, rerun tests and boot once, publish (`pwsh .weaver\publish.ps1`; humanizer pass on new docs first).
2. Finish S18 (latency is the top issue for mouse play) and the S4f visual bugs.
3. Then: FSR 3.1/DLSS/XeSS need motion vectors (S14.md says what it takes); AMD Anti-Lag 2 untested (no AMD GPU); HDR untested on a real HDR display.

## Shortcomings to fix
- High refresh and mouse aim still need gameplay verification (S13).
- Licence texts missing in the release for Eden/yuzu GPL-2.0 snippets, libc++abi, MSVC runtime.
- README build-from-source uses junctions (base\recomp etc.); verify on a fresh clone or make the scripts find base/ directly.
- Timing-sensitive tests (kernel_threads, svc_info, gfx_nvn_scene_stress, watchdog) can fail under heavy machine load and pass alone; gfx_nvn_scene_texture depends on the bc7_cache contents in its build folder.
- New dev docs (S8-S18) have not had the plain-language pass yet.

## Decisions that matter
GPL-3.0; recompile main+sdk+subsdk0 with HLE at SVC/IPC plus hook overrides (movie→Media Foundation, GetNpadState, fs as folder); Ryujinx shader translator, SPIR-V shipped; ASTC→BC7 at setup; Vulkan 1.3; variable timestep; prebuilt exe release, player supplies dump; Windows x64 only; repos public; local tooling files stay out of the published history (publish.ps1 scrubs them).
