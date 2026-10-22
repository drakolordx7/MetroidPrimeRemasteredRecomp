# Status: Metroid Prime Remastered PC recomp

## Done
- Toolkit (`.weaver\check-toolchain.ps1`), guard hook, Eden reference emulator, 010 Editor, Superluminal.
- Recompiler (`recomp/`): difftest 565,061/565,061, mutation 22/22, e2e 30/30, hooks; oracles locked. Lifts and compiles main/sdk/subsdk0/rtld (138,502 functions) in about 2 minutes.
- Offline graphics tools (`tools/`): shader harness, ASTC→BC7, tiling; oracles locked.
- Runtime main: ABI 3, C++ exceptions, graphics shell, Horizon services (fs/RomFS, saves, am, acc, set, time, hid, pl, audren, vi, nvdrv and stubs), NVN on Vulkan (513/523 entry points, all 204 the game uses), shader cache (67,506 blocks, 0 failures). 122/122 tests.
- Knowledge base (`docs/mpr/`), asset survey (`docs/mpr/survey/SURVEY.md`).
- Boot: the real game runs its startup, nnMain, file system and save mount, all startup services, and starts its graphics thread. Last stop: NVN init in the SDK's own driver (being rerouted to our backend).
- GitHub: both repos humanized and published (private).

## Running
- Boot integration (branch `boot2`): route nvnBootstrapLoader to our NVN backend, root-cause the lazy PLT resolver crash (debug 018), real thread info, load-robust timing tests.
- Test tooling and Eden references (branch `testtools`).
- Player setup tool (`tools/setup`).

## Next (in this order)
1. Mouse and keyboard: raw mouse via CPlayerMP1::ProcessInput, KB+M via nn::hid::GetNpadState, bindings file and rebinding UI.
2. High refresh: patch CGameArchitectureSupport::Update (1/60), physics probe at 60/120/240, then dt fixes or interpolation.
3. Display: resolution, aspect and HUD (COsContext::GetScreen*, CDisplayManager::GetAspectRatio), FOV (CGameCameraMP1::UpdateFOV), dynamic resolution off, quality options.
4. Movies via Media Foundation, audio renderer correctness.
5. NVN gaps: sparse textures (MapVirtual), transform feedback, occlusion queries, pipeline prewarm.
6. Extras: HDR (NTonemap), FSR 3.1, DLSS/XeSS, Reflex/Anti-Lag 2.

## Open items
- Superluminal licence activation for its llm/mcp modes (browser step).
- `.weaver/INDEX.md` needs a plain-language pass once its pending edits are committed.

## Decisions that matter
GPL-3.0; recompile main+sdk+subsdk0 with HLE at SVC/IPC plus hook overrides (movie→Media Foundation, GetNpadState, fs as folder); Ryujinx shader translator, SPIR-V shipped; ASTC→BC7 at setup; Vulkan 1.3; prebuilt exe release, player supplies dump; Windows x64 only; repos private until release; AI tooling files (CLAUDE.md, .claude, brief preamble) stay local.
