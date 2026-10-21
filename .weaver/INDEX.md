# Tool index

Project-local tools (one line each: what it does, how to run).

- `toolchain/hactool/hactool.exe` — unpack NCA/NSP/XCI (needs prod.keys). `hactool -k prod.keys ...`
- `toolchain/nstool/nstool.exe` — inspect/extract NSP, XCI, NCA, NSO. `nstool <file>`
- `.weaver/check-toolchain.ps1` — verifies every installed tool runs; exit code = failures. `pwsh .weaver\check-toolchain.ps1`
- `toolchain/nx2elf/nx2elf.exe` — NSO/NRO → ELF for IDA. `nx2elf <nso> --export-elf <out>` (built from `toolchain/src/nx2elf`)
- `toolchain/retrotool/retrotool.exe` — MPR .pak / TXTR / FMV0 extract and repack (built from `refs/retrotool`)
- `refs/PrimeRemasterStructs/*.bt` — 010 Editor templates for 48 MPR asset formats
- `toolchain/eden/eden.exe` (+ `eden-cli.exe`) — Eden v0.2.1 Switch emulator (official git.eden-emu.dev build, Defender-clean), the reference oracle for traces and frame comparisons
- `.claude/hooks/guard.py` — PreToolUse guard: no game data in git/uploads, read-only refs/game/toolchain, locked oracles (`oracle/LOCKED`). Self-test: `python .claude/hooks/test_guard.py`
- `runtime/scripts/build.ps1` — build the runtime + run CTest. `pwsh runtime\scripts\build.ps1 -Clean -Test`
- `tools/{tiling,shaders,textures}/oracle/run_oracle.py` — S4 tool oracles (locked); see `tools/.weaver/INDEX.md` for the per-tool commands
- `.weaver/publish.ps1` — sync recomp/runtime/tools into `publish/nxrecomp` (subtree), push github.com/drakolordx7/nxrecomp, bump + push the game repo github.com/drakolordx7/MetroidPrimeRemasteredRecomp (both private). Push only on the user's say-so.
- `tools/.venv` — Python 3.13 with unicorn, capstone, lz4, pyelftools (lifter oracle, NSO parsing). `tools\.venv\Scripts\python`
- `refs/ryubing/src/Ryujinx.Graphics.Shader` — Ryujinx MIT shader translator source (Codeberg archive a82350bb77, 2026-07-17); build with .NET 10.

- 010 Editor 16.0.4 (`C:\Program Files\010 Editor\010Editor.exe`) — run `refs/PrimeRemasterStructs/*.bt` on MPR files headless: `-script:x.1sc -noui -nowarnings`, script uses `RunTemplate` + `OutputPaneSave`
- Superluminal (`C:\Program Files\Superluminal\Performance\SuperluminalCmd.exe`) — CPU profiler; `run`/`attach` capture, `llm` analysis and global `superluminal` MCP (llm/mcp need license activation)

Global (machine-wide) tools used here: IDA Pro 9.4 + ida-mcp plugin, mcp-windbg plugin, renderdoc-mcp (`%LOCALAPPDATA%\Programs\renderdoc-mcp`), LLVM, CMake, Ninja, sccache, Vulkan SDK, RenderDoc, VS Build Tools 2026.

S2 knowledge base (docs/mpr/, scripts in tools/analysis/):
- `tools\.venv\Scripts\python tools\analysis\kb_rebuild.py [--elf work\elf\main.elf]` — rebuild docs/mpr from frag/*.json (headers, patches, check, merge) and, with --elf, validate and write verification blocks back
- `tools\analysis\validate_kb.py --elf work\elf\main.elf [--write-back] [--quiet]` — PASS/FAIL/WARN per symbol, patch, vtable and field claim against the real main; needs LLVM llvm-cxxfilt
- `tools\analysis\ida_kb_apply.py work\elf\main.elf --out work\ida\main.i64` — headless idalib: apply structs.h, names and comments from docs/mpr (rerun on the saved .i64 after a rebuild)
- `tools\analysis\sym_find.py work\elf\main.elf "<regex>" [--imports] [--callers]` — search demangled symbols with address, size and direct callers
- `tools\analysis\pak_census.py game\romfs [--json out]` — asset-type and TXTR-format census from pak headers only
- `tools\analysis\tests\run_synth.py` and `run_ida_synth.py` — prove validator and IDA apply on a synthetic AArch64 ELF (clang + lld)
- `tools\analysis\kb_check.py frag.json` — schema + evidence-in-source oracle for fragments; `kb_parse_headers.py`, `kb_merge.py`, `kb_build_patches.py`, `kb_harvest_port.py`, `kb_pairs_port.py` are the pipeline steps
