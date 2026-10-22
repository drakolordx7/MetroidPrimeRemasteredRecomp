# Status: Metroid Prime Remastered PC recomp

## Done
- Toolkit (`.weaver\check-toolchain.ps1`), guard hook, Eden reference emulator, 010 Editor, Superluminal.
- Recompiler (`recomp/`): difftest 565,061/565,061, mutation 22/22, e2e 30/30, hooks; oracles locked. Lifts and compiles main/sdk/subsdk0/rtld (138,502 functions) in about 2 minutes.
- Offline graphics tools (`tools/`): shader harness, ASTC→BC7, tiling; oracles locked.
- Runtime main: ABI 3, C++ exceptions, graphics shell, Horizon services (fs/RomFS, saves, am, acc, set, time, hid, pl, audren, vi, nvdrv and stubs), NVN on Vulkan (513/523 entry points, all 204 the game uses), shader cache (67,506 blocks, 0 failures). 122/122 tests.
- Knowledge base (`docs/mpr/`), asset survey (`docs/mpr/survey/SURVEY.md`).
- Boot: the real game reaches the title screen ("PRESS A TO START", background still black) and main menu through our NVN-on-Vulkan backend at about 136 fps headless, and with scripted input the loading screen, where the Vulkan device is lost (~58 s). Screenshot: work\run\shot_0.png.
- GitHub: both repos humanized and published (private).

## Running
- NVN correctness to gameplay (branch `nvn2`): struct-size audit, validation clean, fix the device loss, title background, past loading into gameplay.
- Test tooling and Eden references (branch `testtools`).
- Player setup tool (`tools/setup`).

## Next (in this order)
1. Play mode: real window, SDL event pump and frame limiter on the guest main thread, real controller input into hid (today mpr.exe is headless with scripted presses).
2. Mouse and keyboard: raw mouse via CPlayerMP1::ProcessInput, KB+M via nn::hid::GetNpadState, bindings file and rebinding UI.
3. High refresh: patch CGameArchitectureSupport::Update (1/60), physics probe at 60/120/240, then dt fixes or interpolation.
4. Display: resolution, aspect and HUD (COsContext::GetScreen*, CDisplayManager::GetAspectRatio), FOV (CGameCameraMP1::UpdateFOV), dynamic resolution off, quality options.
5. Movies via Media Foundation, audio renderer correctness.
6. NVN gaps: sparse textures (MapVirtual), transform feedback, occlusion queries, pipeline prewarm.
7. Extras: HDR (NTonemap), FSR 3.1, DLSS/XeSS, Reflex/Anti-Lag 2.

## Shortcomings to fix
- gfx_nvn_scene_stress failed once under load, passed alone; watch it.

## Open items
- Superluminal licence activation for its llm/mcp modes (browser step).
- `.weaver/INDEX.md` needs a plain-language pass once its pending edits are committed.

## Decisions that matter
GPL-3.0; recompile main+sdk+subsdk0 with HLE at SVC/IPC plus hook overrides (movie→Media Foundation, GetNpadState, fs as folder); Ryujinx shader translator, SPIR-V shipped; ASTC→BC7 at setup; Vulkan 1.3; prebuilt exe release, player supplies dump; Windows x64 only; repos private until release; AI tooling files (CLAUDE.md, .claude, brief preamble) stay local.
