# Metroid Prime Remastered — native PC static recompilation

## Context
Goal: turn the Switch release of Metroid Prime Remastered (MPR, title 010012101468C000, v1.0.0 — the only version ever shipped, build ID 67C9CA14…) into a native Windows x64 executable. Must-haves: arbitrary resolution, high refresh rate (120 fps and beyond), raw mouse input, full keyboard+mouse play. Optional, last: upscaling and frame generation.

Why this is feasible now (research, Oct 2026):
- ~10 open Switch static recomps exist and run real games at 60 fps: ssbu-recomp (Smash, GPL-3), smo-recomp (Odyssey, GPL-3, best docs), SuperMarioWonderRecomp (MIT runtime), LASRecomp (Link's Awakening, built almost entirely with Claude Code), ScarletNX (generic recompiler library). The pattern is proven: AArch64 → C++ lifting, guest image mapped at native base, NVN reimplemented on Vulkan, Maxwell shaders translated ahead of time.
- MPR specifics are favourable: one binary version, NVN confirmed, C++ symbol names very likely present (mods hook by mangled name), game logic is the original Prime engine (`CPlayerMP1`, `CFirstPersonCameraMP1`…) so PrimeDecomp + MetroidPrimePort + mp1r-practice-mod supply names, struct layouts, input structure (`CFinalInput`) and a high-FPS audit.
- Nobody has published an MPR decomp/recomp/port.

Machine: i9-12900K, 64 GB RAM, RTX 3080, ~118 GB free on D:. Missing: LLVM/clang, CMake, Ninja, VS Build Tools + Windows SDK, Vulkan SDK, JDK 21 (only JDK 8 present), Ghidra, Switch tools.

## Approach (decisions taken unless flagged OPEN)
- **Recompile everything, HLE at the OS boundary.** Lift `main`, `sdk`, `subsdk*` to C++. Reimplement Horizon SVCs and IPC services (fs, hid, time, settings, account, save, audio out, nvservices stubs). Override selected `nn::` functions with host-native versions where it is better (NVN, fs, hid, allocator, threads).
- **Graphics: NVN → Vulkan 1.3** via the `nvnBootstrapLoader` entry point; replay command buffers; block-linear untiling; ASTC transcoded to BC7 (desktop GPUs lack ASTC); Maxwell shaders → SPIR-V ahead of time with Ryujinx's MIT shader translator (dotnet tool), shipped as a hash-keyed cache, so no compile stutter.
- **Audio:** run the SDK's own audio renderer code in-process (recompiled), output via SDL3; Ryujinx Amadeus as reference.
- **Input:** SDL3 3.4.x relative mouse mode (hardware raw input, no acceleration). Mouse deltas injected directly into the aim code (player yaw rotation + free-look pitch clamped by `gpTweakPlayer->GetMaxFreeLookPitchAngle()`), not faked as stick input. Controllers via SDL3 gamepad, gyro kept.
- **High refresh: variable timestep**, not 60 Hz logic + interpolation. Lowest input latency (matters for mouse feel); game update functions already take `float dt`. Fix the per-tick systems listed in MetroidPrimePort's HIGH_FPS_AUDIT (player/morph-ball friction, projectile tick period, decals, AI frame counters, HUD message countdown) after mapping them to MPR. dt clamped; fallback to interpolation only for any system that cannot be made dt-correct.
- **Resolution:** arbitrary internal resolution and aspect (16:9, 21:9, 32:9), HUD kept at correct aspect, dynamic resolution off (known single-instruction patch at 0xAFF5D4), LOD bias and AA options (offsets known from theboy181/cucholix patches).
- **Upscaling/frame gen (last phase, optional):** FSR 3.1 (MIT, Vulkan, upscale + frame gen) built-in; DLSS and XeSS loaded from user-supplied DLLs.
- **Public GitHub release, Windows x64 only.** Release ships a prebuilt exe (recompiled code inside, Zelda64Recomp/Unleashed style); the player supplies their own dump. A first-run setup tool takes their NSP/XCI + keys (or already-extracted RomFS), checks the build ID / file hashes against 1.0.0, and extracts RomFS into the game folder. No game assets or keys in the repo or release.
- **Licence: GPL-3.0.** Open release makes GPL free to adopt, which unlocks the most mature Windows runtime (ssbu-recomp / smo-recomp lifter + NVN-on-Vulkan) while still taking MIT code (Ryujinx shader translator, SuperMarioWonderRecomp pieces). Base: fork smo-recomp's architecture (documented, single-player game, 60 fps proven), borrow from ssbu-recomp's lifter test suite.
- **Disassembler: IDA Pro 9.4** (installed) via Hex-Rays' official ida-mcp plugin, headless idalib; game executables converted with nx2elf first. Ghidra 12.1.2 + Switch Loader only as a fallback/second opinion, not installed.
- **Dump not yet available.** Phase 0 and the game-independent parts (toolkit, reference study, lifter + Unicorn test suite, runtime skeleton, SDL3/Vulkan shell, setup tool) start without it. Phase 1 analysis starts the moment the dump lands.

## Toolkit (`.weaver/`, built and installed in Phase 0)
- Build: LLVM/clang-cl, CMake, Ninja, sccache, VS Build Tools + Windows SDK, Vulkan SDK.
- Analysis: Ghidra 12.1.2 + Adubbz Switch Loader + pyghidra-mcp (headless, agent-driven); JDK 21; nx2elf; hactool/nstool; retrotool (MPR asset formats); BinDiff (carry PrimeDecomp names); Capstone + Unicorn (Python).
- Debug/verify: mcp-windbg (recompiled exe), renderdoc-mcp (graphics capture diff/pixel asserts), Ryubing with GDB stub (reference traces from the real game), Vulkan validation layers.
- Claude plugins: official `clangd-lsp`, `ralph-loop`; the "Reverse Engineering" directory skill.
- Own tools (small scripts): dump extractor, function-list builder, lifter test harness, trace differ, build-shard generator, shader-cache builder, fps physics probe.
- Reference clones: ssbu-recomp, smo-recomp, SuperMarioWonderRecomp, LASRecomp, ScarletNX, prime-recomp, MetroidPrimePort, mp1r-practice-mod, MP1R-Exlaunch-Base, retrotool, PrimeDecomp, Ryujinx.

## AI workflow (lessons from LASRecomp, ssbu-recomp, momo5502's agent decomp write-up, Snowboard Kids 2)
- Oracle before scale: every agent loop has a machine-checked PASS/FAIL (Unicorn lifter diffs, state-hash traces vs Ryubing, RenderDoc pixel asserts).
- Anti-cheat: checker scripts hashed and verified each batch; no inline asm; agents can't edit oracles.
- Per-item headless loops (`claude -p` / ralph-loop): take the easiest failing item, cap attempts, log give-ups for a manager.
- Lifting is mechanical (deterministic tool, no AI); AI effort goes to HLE services, NVN, shader edge cases, MPR-specific fixes and naming.
- Byte-matching decomp is out (different CPU and compiler from PrimeDecomp); PrimeDecomp is used for names and struct layouts only.

## Phases and milestones
0. **Setup** — install toolkit, clone references, git repo per major folder (`recomp/`, `runtime/`, `tools/`), `.weaver/` index/status/changelog.
1. **Dump intake + analysis** — extract ExeFS/RomFS from user dump, NSO→ELF, confirm build ID, symbols, compiler, import list (NVN, nn:: services). Ghidra project. Function list from `.eh_frame` + symbols; jump tables resolved via Unicorn. Name/struct recovery from symbols, RTTI, PrimeDecomp, practice-mod headers. *Done when: complete function table and import list.*
2. **Recompiler** — fork/adapt chosen base lifter; Unicorn differential tests (tens of thousands of instruction cases, checker hashed so agents can't weaken it, no inline asm); indirect-call dispatch table; output sharded across many TUs. *Done when: all of main+sdk lift and link.*
3. **Runtime/HLE** — loader, guest memory at native base, threads with a 3-core scheduling model, sync, SVCs, IPC services, RomFS as local folder, saves to `%APPDATA%`. *Done when: boots to first NVN call.*
4. **Graphics + audio** — NVN on Vulkan, untiling, BC7 transcoding, AOT shader cache, audio. *Done when: title screen renders with sound.*
5. **Playable** — iterate with oracles: per-frame state-hash diff against Ryubing traces, RenderDoc image diffs. *Done when: Frigate Orpheon to credits playthrough clean.*
6. **PC features** — resolution/aspect/HUD, uncapped + 120/144/240 + VRR + limiter, variable-dt fixes, raw mouse aim, full KB+M binding set (visors, beams, morph ball, lock-on, scan), rebinding, in-game settings overlay (ImGui). *Done when: physics probe shows identical walk speed/jump height/morph friction at 60/120/240, mouse aim 1:1 with no smoothing.*
7. **Optional extras** — FSR 3.1 upscale + frame gen, DLSS/XeSS hooks.

## Team
Lead (this session) owns architecture and integration. Managers per stream once Phase 1 is done: recompiler+oracle, runtime/HLE, graphics+shaders, later PC features. Workers for extraction, scripts, test runs, contained edits.

## Verification
- Lifter: Unicorn differential suite, run every batch.
- Runtime: boot milestones above; state-hash traces vs Ryubing for the same inputs.
- Graphics: RenderDoc captures vs emulator frames; Vulkan validation clean.
- High FPS: scripted physics probe at 60/120/240; frame-time logs.
- Mouse: raw delta log vs in-game yaw/pitch, confirm linear and unsmoothed.
- Screenshots at first boot, title screen, first gameplay, each feature batch.

## Risks
Shader count and specialization; thread timing; ASTC transcoding cost; build size (~1+ GB generated C++, long first build); SDK coverage gaps. All handled by the oracles above rather than guesswork.
