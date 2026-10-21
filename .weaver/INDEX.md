# Tool index

Project-local tools (one line each: what it does, how to run).

- `toolchain/hactool/hactool.exe` — unpack NCA/NSP/XCI (needs prod.keys). `hactool -k prod.keys ...`
- `toolchain/nstool/nstool.exe` — inspect/extract NSP, XCI, NCA, NSO. `nstool <file>`
- `.weaver/check-toolchain.ps1` — verifies every installed tool runs; exit code = failures. `pwsh .weaver\check-toolchain.ps1`
- `toolchain/nx2elf/nx2elf.exe` — NSO/NRO → ELF for IDA. `nx2elf <nso> --export-elf <out>` (built from `toolchain/src/nx2elf`)
- `toolchain/retrotool/retrotool.exe` — MPR .pak / TXTR / FMV0 extract and repack (built from `refs/retrotool`)
- `refs/PrimeRemasterStructs/*.bt` — 010 Editor templates for 48 MPR asset formats
- `tools/.venv` — Python 3.13 with unicorn, capstone, lz4, pyelftools (lifter oracle, NSO parsing). `tools\.venv\Scripts\python`
- `refs/ryubing/src/Ryujinx.Graphics.Shader` — Ryujinx MIT shader translator source (Codeberg archive a82350bb77, 2026-07-17); build with .NET 10.

Global (machine-wide) tools used here: IDA Pro 9.4 + ida-mcp plugin, mcp-windbg plugin, renderdoc-mcp (`%LOCALAPPDATA%\Programs\renderdoc-mcp`), LLVM, CMake, Ninja, sccache, Vulkan SDK, RenderDoc, VS Build Tools 2026.
