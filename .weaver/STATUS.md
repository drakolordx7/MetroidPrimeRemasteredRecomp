# Status: Metroid Prime Remastered PC recomp

## Done
- Phase 0 toolkit (`.weaver\check-toolchain.ps1`), guard hook, Eden reference emulator, 010 Editor, Superluminal.
- S1 recompiler (`recomp/`): difftest 565,061/565,061, mutation 22/22, e2e 30/30, hooks; oracles locked.
- S4 offline graphics tools (`tools/`): shaders harness, ASTC→BC7, tiling; oracles locked.
- S3 runtime skeleton + S3b ABI v2 and C++ unwinder + S4b graphics shell merged on `runtime` main: 54/54 tests.
- S2 knowledge base (`docs/mpr/`): validator on real main 2,247 PASS / 5 FAIL (source errors) / 462 WARN; IDA db `work\ida\main.i64`.
- Dump gate: v1.0.0 confirmed (build ID 67C9CA14…), SDK 12.3.1, 92,784 named functions, lifter coverage 100% of 6.5 M instructions, FPCR unused by game code. Asset survey (`docs/mpr/survey/SURVEY.md`): Ryujinx translator chosen, no Scaleform, DSP-ADPCM audio, H.264 movies, about 12-23 min ASTC→BC7.
- GitHub: private drakolordx7/nxrecomp (base) and drakolordx7/MetroidPrimeRemasteredRecomp (game, base as submodule); `.weaver\publish.ps1`.

## In progress
- S1b: lift + compile main/sdk/subsdk0 (work\lift, work\build), plus 4 lifter changes requested by S3b.
- S3c: boot-path Horizon services (branch `services`).
- S4d: NVN→Vulkan implementation + full 67,506-block shader cache (branch `nvn`).

## Running
- S3c services (branch `services`), S4d NVN→Vulkan (branch `nvn`), S5 test tooling and Eden references (branch `testtools`).

## Next (in this order)
1. Boot integration loop: merge services/nvn, run tools\boot\boot.py, route blockers.
2. S7 setup tool: NSP/XCI + keys import, build-ID check, RomFS extract, in-process ASTC→BC7 cache, shader cache install.
3. S6-PC input: raw mouse via CPlayerMP1::ProcessInput trampoline, KB+M via nn::hid::GetNpadState import, bindings file + ImGui rebinding.
4. High-fps experiment: patch CGameArchitectureSupport::Update 1/60, physics probe at 60/120/240, then variable-dt fixes or interpolation.
5. Display: resolution/aspect/HUD (COsContext::GetScreen*, CDisplayManager::GetAspectRatio), FOV (CGameCameraMP1::UpdateFOV), dynamic-res off, quality options.
6. Movies via Media Foundation (movie:: imports in subsdk0), audio renderer correctness.
7. Extras: HDR (NTonemap), FSR 3.1, DLSS/XeSS, Reflex/Anti-Lag 2.

## Shortcomings to fix
- kernel_threads and gfx_pacing tests fail under heavy machine load (pass alone): make them load-robust.

## Open items
- Superluminal license activation for its llm/mcp modes (needs a browser step).
- BinExport for IDA 9.4 not built (not needed so far).
- PIXLD.MY_INDEX lowering (S4d investigating).

## Decisions that matter
GPL-3.0; recompile main+sdk+subsdk0, HLE at SVC/IPC with hook overrides (movie→Media Foundation, GetNpadState, fs as folder); smo lifter + Wonder/ssbu/ScarletNX pieces; Ryujinx shader translator, SPIR-V shipped; ASTC→BC7 at setup; Vulkan 1.3; prebuilt exe release, player supplies dump; Windows x64 only; repos private until release; symbol names/addresses in docs are kept.
