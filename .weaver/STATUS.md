# Status — Metroid Prime Remastered PC recomp

## Done
- Phase 0 toolkit installed and verified (`.weaver\check-toolchain.ps1`, 16/16 pass): LLVM 23.1.4, CMake 4.4.4, Ninja, sccache, VS Build Tools 2026 + Windows SDK 26100, Vulkan SDK 1.4.363, RenderDoc 1.46, WinDbg (cdb), .NET 10, Rust, hactool, nstool, nx2elf (built), retrotool (built), Python oracle venv (Unicorn, Capstone), IDA Pro 9.4 + idalib.
- Ryujinx shader translator (MIT) builds from the Codeberg Ryubing archive.
- Global Claude add-ons: ida-mcp, mcp-windbg, renderdoc-mcp, clangd-lsp, ralph-loop, Trail of Bits modern-cpp / differential-review / regression-hunt / c-review.
- 18 reference projects in `refs/` (Switch recomps, Prime ports/mods, retrotool, PrimeRemasterStructs, Ryubing, deko3d, XenonRecomp, N64Recomp).
- Git repos: root, `recomp/`, `runtime/`, `tools/`.

## In progress
- Ryubing emulator built from source as the reference oracle (git.ryujinx.app unreachable).

## Next
- Game-independent work while the dump is pending: study smo-recomp / ssbu-recomp / Wonder architecture, then lifter + Unicorn test suite, runtime skeleton, SDL3/Vulkan shell, first-run setup tool.
- Phase 1 the moment the user's dump (NSP/XCI + prod.keys) arrives.

## Open items
- "Reverse Engineering" directory skill: user installs from the claude.ai card (CLI can't find it).
- BinDiff/BinExport: no BinExport build for IDA 9.4 yet; build from source against the IDA SDK in Phase 1 if name matching needs it.
- PrimeDecomp server (git.axiodl.com) returns 502; decomp source is available inside `refs/MetroidPrimePort/decomp`.

## Decisions that matter
GPL-3.0; base on smo-recomp architecture; IDA primary, Ghidra not installed; variable timestep for high refresh; Vulkan 1.3; FSR 3.1 built-in, DLSS/XeSS user DLLs; prebuilt exe release, player supplies dump; Windows x64 only.
