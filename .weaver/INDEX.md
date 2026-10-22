# Tool index

Project-local tools (one line each: what it does, how to run).

- `toolchain/hactool/hactool.exe` — unpack NCA/NSP/XCI (needs prod.keys). `hactool -k prod.keys ...`
- `toolchain/nstool/nstool.exe` — inspect/extract NSP, XCI, NCA, NSO. `nstool <file>`
- `.weaver/check-toolchain.ps1` — verifies every installed tool runs; exit code = failures. `pwsh .weaver\check-toolchain.ps1`
- `toolchain/nx2elf/nx2elf.exe` — NSO/NRO → ELF for IDA. `nx2elf <nso> --export-elf <out>` (built from `toolchain/src/nx2elf`)
- `toolchain/retrotool/retrotool.exe` — MPR .pak / TXTR / FMV0 extract and repack (built from `refs/retrotool`)
- `refs/PrimeRemasterStructs/*.bt` — 010 Editor templates for 48 MPR asset formats
- `toolchain/eden/eden.exe` (+ `eden-cli.exe`) — Eden v0.2.1 Switch emulator (official git.eden-emu.dev build, Defender-clean), the reference oracle for traces and frame comparisons
- Oracle folders that contain an `oracle/LOCKED` file are hash-locked (`oracle/SHA256SUMS`): do not edit them.
- `runtime/scripts/build.ps1` — build the runtime + run CTest. `pwsh runtime\scripts\build.ps1 -Clean -Test`
- `tools/{tiling,shaders,textures}/oracle/run_oracle.py` — S4 tool oracles (locked); see `tools/.weaver/INDEX.md` for the per-tool commands
- `.weaver/publish.ps1` — sync recomp/runtime/tools into `publish/nxrecomp` (subtree), push github.com/drakolordx7/nxrecomp, bump + push the game repo github.com/drakolordx7/MetroidPrimeRemasteredRecomp (both private). Push only on the user's say-so.
- `tools/.venv` — Python 3.13 with unicorn, capstone, lz4, pyelftools (lifter oracle, NSO parsing). `tools\.venv\Scripts\python`
- `refs/ryubing/src/Ryujinx.Graphics.Shader` — Ryujinx MIT shader translator source (Codeberg archive a82350bb77, 2026-07-17); build with .NET 10.

- 010 Editor 16.0.4 (`C:\Program Files\010 Editor\010Editor.exe`) — run `refs/PrimeRemasterStructs/*.bt` on MPR files headless: `-script:x.1sc -noui -nowarnings`, script uses `RunTemplate` + `OutputPaneSave`
- Superluminal (`C:\Program Files\Superluminal\Performance\SuperluminalCmd.exe`) — CPU profiler; `run`/`attach` capture

Global (machine-wide) tools used here: IDA Pro 9.4, WinDbg, LLVM, CMake, Ninja, sccache, Vulkan SDK, RenderDoc, VS Build Tools 2026.

S2 knowledge base (docs/mpr/, scripts in tools/analysis/):
- `tools\.venv\Scripts\python tools\analysis\kb_rebuild.py [--elf work\elf\main.elf]` — rebuild docs/mpr from frag/*.json (headers, patches, check, merge) and, with --elf, validate and write verification blocks back
- `tools\analysis\validate_kb.py --elf work\elf\main.elf [--write-back] [--quiet]` — PASS/FAIL/WARN per symbol, patch, vtable and field claim against the real main; needs LLVM llvm-cxxfilt
- `tools\analysis\ida_kb_apply.py work\elf\main.elf --out work\ida\main.i64` — headless idalib: apply structs.h, names and comments from docs/mpr (rerun on the saved .i64 after a rebuild)
- `tools\analysis\sym_find.py work\elf\main.elf "<regex>" [--imports] [--callers]` — search demangled symbols with address, size and direct callers
- `tools\analysis\pak_census.py game\romfs [--json out]` — asset-type and TXTR-format census from pak headers only
- `tools\analysis\tests\run_synth.py` and `run_ida_synth.py` — prove validator and IDA apply on a synthetic AArch64 ELF (clang + lld)
- `tools\analysis\kb_check.py frag.json` — schema + evidence-in-source oracle for fragments; `kb_parse_headers.py`, `kb_merge.py`, `kb_build_patches.py`, `kb_harvest_port.py`, `kb_pairs_port.py` are the pipeline steps
- `tools/survey/*` — S4c asset-survey scripts (pak extract, inventory, shader/texture/movie/audio/UI probes); index in `tools/.weaver/INDEX.md`, results in `docs/mpr/survey/SURVEY.md`
- `runtime/tests/tools/native_check.cmd <prog.cpp>` — S3b: build one `runtime/tests/lift/progs` exception program for the host, run it and print its results[] (the expected output of the lifted run). `runtime/tests/tools/guest_build.py <src> <out.elf>` compiles one for AArch64 the way the oracle does.
- `ctest --test-dir runtime\build\release -R lift_` — S3b: lifts and runs all of S1's e2e programs plus the exception programs on the real runtime (build first: `pwsh runtime\scripts\build.ps1`); results[] must equal Unicorn / host exceptions. Single program: `runtime\build\release\tests\lift\bin\liftrun_<name>.exe --elf ...\<name>.elf --expected ...\<name>.expected`
- S1b (recomp, Phase 3 lift + compile): `recomp\scripts\build_mpr.cmd` lifts main/sdk/subsdk0/rtld into `work\lift` and builds the four static libraries into `work\build\mpr` (own sccache on port 24339 in `work\build\sccache`); `... --target mpr_link_check` links them with stubs. Docs: `recomp/docs/S1b.md`.
- `.weaver\peakmem.py -- <cmd>` — run a command in a job object: wall, CPU, peak commit, free disk (set `MSYS2_ARG_CONV_EXCL=*` under git bash). `.weaver\lift_stats.py <nso> <name> <0xbase>` and `br_classify.py` (cwd recomp/) — discovery/jump-table/LSDA/gap statistics; `modfacts.py [--imports-out DIR]` — NSO layout, init arrays, relocations, imports and providers; `ninja_times.py <build dir>` — compile time per module.
- S6 (first boot): `tools\.venv\Scripts\python tools\boot\boot.py [--libs] [--probe no-sdk-services] [--stub-result 0] [--link host] [--grep RE] [--seconds N]` — rebuild mpr.exe (`pwsh game-build\scripts\build.ps1`), run it headless in `work\run` with a timeout, print stop reason + named guest call stack, unknown SVCs / stub IPC commands (with raw bytes) / NVN stubs / HLE stubs, last log lines. `tools\boot\addrname.py 0x7500148900 ...` — guest address to demangled symbol; `nso_info.py <nso> [--dis off count]` — NSO header + disassembly of a module range; `nso_tpidr.py`, `svc_sites.py` — TLS register and SVC-number census of an NSO. Docs: `runtime/docs/S6.md`.

S3c (services) tools, in runtime\scripts unless noted:
- `pwsh runtime\scripts\t.ps1 <group> ...` — build nxrt_tests and run the named test groups directly (`-All` runs everything, `-NoBuild` skips the build). Groups: svc_* (services), svc_audren_* (audio renderer port).
- `pwsh runtime\scripts\wt_setup.ps1 -Name <n>` — sibling git worktree on branch <n> with a gfx-off build configured against recomp\include (fast test builds).
- `python -I runtime\scripts\svc_table.py --out runtime\docs\S3c_commands.md` — regenerates the service command table from src\services.
- `runtime-wt\gb-services\run.sh [boot.py args]` — builds mpr.exe with the services worktree's runtime and runs the real game headless (tools\boot\boot.py copy writing to work\run_svc); `SECS=`, `LVL=`, `N=`, `T=` env vars set timeout, log level, summary lines, ipc tail lines.
- `pwsh runtime\scripts\nvn_unit.ps1 -Src <test.cpp>` — builds and runs one NVN unit test without CMake; `python runtime\scripts\gen_nvn_test_api.py` (typed NVN callers for tests), `gen_nvn_coverage_doc.py coverage.tsv mpr_used_nvn.txt` (entry-point table for docs/S4d.md; coverage.tsv from `NXRT_NVN_DUMP_COVERAGE=<file> nxrt_gfx_tests gfx_nvn_impl`). NVN scene oracles: `NXRT_GFX_HIDDEN=1 nxrt_gfx_tests gfx_nvn_scene_<clear|triangle|geometry|state|texture|commands|msaa|stress>`; `NXRT_GFX_GPU=integrated` for the iGPU.
- S5 test tooling (runtime, branch `testtools`): `NXRT_TEST_SCRIPT=run.nxs NXRT_TEST_OUT=out NXRT_TEST_DETERMINISTIC=1 mpr.exe` runs a scripted run (exit 0 pass / 1 fail / 4 crash / 5 freeze); keys, DSL (`include/nxrt/tt_script.h`), trace and result formats in `runtime/docs/S5.md`, `runtime/docs/CONFIG.md` (`[test]`). Lifted game needs `runtime/tests/sites/mpr_testtools.sites` for the `hook` frame source. Unit groups: `pwsh runtime\scripts\build.ps1 -Test -Filter "tt_"`; pure units without a full build: `runtime\scripts\tt_unit.cmd <group> <sources>`.
- S5 host tools (`tools/test/`, see its README): `run_suite.py suite.toml` (one PASS/FAIL table over scripted runs; `suites/boot.toml`), `imgdiff.py A B [--mask hud]`, `tracediff.py A B`, `regress.py summarize|compare`, `gen_regions.py` (-> `regions.tsv`), all tested with `tools\.venv\Scripts\python -I -m unittest discover -s tools\test\tests`.
- S5 Eden reference (`work/eden`, portable, git-ignored): `tools\test\eden_config.py setup`, `eden_run.py --out work\eden_ref\NAME --every N --seconds S [--timeline t.json]` (frames via the Vulkan screenshot layer, key presses via `edeninput.py`, state via `edengdb.py info|state|trace` on the GDB stub port 6543).

S6b (boot integration, second pass; docs `runtime/docs/S6b.md` on branch boot2):
- `.weaver/boot_wt.sh [boot.py args]` — boot.py against the boot2 runtime worktree (separate build dir `game-build/build/boot2`; `MPR_RUNTIME`/`MPR_BUILD_DIR` env choose the runtime checkout). Boot options via env: `NXRT_HLE_TRACE=nvn` (ordered HLE call trace with results), `NXRT_BOOT_PRESS="A@12,A@22"` (scripted pad), `NXRT_BOOT_SCREENSHOT_AT/EVERY=<s>` (shot_<n>.png in work/run), `NXRT_BOOT_GFX=headless|window|none`, `NXRT_GFX_VALIDATION=1`.
- `tools\.venv\Scripts\python .weaver\nvn_order.py [--seq] [--n N] [mpr.log]` — first-seen order and counts of the hle-trace lines.
- `tools\.venv\Scripts\python .weaver\plt_sym.py work\elf\sdk.elf 0x58b870` — relocation/symbol behind a PLT stub or GOT slot.

S9 (movies and audio, branch `media`, worktree `runtime-wt/media`; docs `runtime/docs/S9.md`):
- `.weaver/boot_media.sh [boot.py args]` — boot.py against the media runtime; builds `game-build-media/` (a copy of game-build at HEAD, so another stream's uncommitted mpr_main.cpp does not matter; build dir `game-build-media/build`), runs in `work/run_media`.
- `.weaver/wtbuild.ps1 <worktree> [target]` — build one target of a runtime worktree and print only the errors.
- `tools\.venv\Scripts\python tools\media\movie_oracle.py [--only ID] [--frame-step N]` — S9 movie oracle: extracts the 25 FMV0 from game\romfs, makes ffmpeg references (frame md5, PCM), runs `nxrt_tests media_movie` (every frame md5, timestamps, audio length) and compares the PCM; work files in `work\media_fmv`.
- `tools/media/{fmv_manifest,fmv_reference,compare_pcm,wav_check}.py` — movie manifest, ffmpeg references, PCM compare (lag/correlation per channel), WAV sanity check (rate, channels, silence, clicks, dropouts); tests next to them (`python -I -m unittest` in tools\media).

S8 (play mode, branch `play`, worktree runtime-wt/play; docs `runtime/docs/S8.md`):
- `.weaver/boot_play.sh [boot.py args]` — boot.py against the play worktree (build dir game-build/build/play). Window run: `--env NXRT_BOOT_GFX=window`; boot.py is headless by default now.
- `pwsh .weaver\play_tests.ps1 [-Filter regex]` — build nxrt_tests + nxrt_gfx_tests in runtime-wt\play and run the play/tt/hid/platform CTest groups.
- `runtime-wt/play/scripts/play_unit.ps1 -Name n -Test t.cpp -Src a.cpp,b.cpp` — one play unit test without CMake; `play_syntax.ps1 files...` — compile check only.
- `tools\.venv\Scripts\python tools\test\run_suite.py tools\test\suites\play.toml --exe game-build\build\play\mpr.exe` then `tools\test\play_check.py suite work\suite_out_play` — title-screen key vs pad oracle, window lifecycle, limiter, settings, overlay.
- `tools\.venv\Scripts\python .weaver\gdis.py 0xADDR [count]` — disassemble main.elf at a vaddr (capstone).
- `.weaver/hifps_wt.sh [boot.py args]` — S11: boot.py against the hifps runtime worktree (`runtime-wt/hifps`, build dir `game-build/build/hifps`).
- `.weaver/killmine.sh` — kill the running mpr.exe of the nvn2 build tree (run before every `trun.sh`: a live exe blocks the rebuild); `.weaver/trun.sh <sec>` with `TRACE=<present>` or `--env NXRT_NVN_TRACE_AFTER_FS=<fs hash prefix>`, `NXRT_NVN_TRACE_SNAP_FS`, `NXRT_NVN_TRACE_SNAP_SAMPLED=1` — traced run of the nvn2 build (docs/S4e.md)
- `.weaver/relift_hifps.cmd` — S11: re-lift + build mpr_main with the current main.sites into work/lift_hifps and work/build/mpr_hifps (shared work/lift untouched); `.weaver/hifps_game_build.cmd` then builds mpr.exe against it into game-build/build/hifps.

S14 (extras, branch `extras`, docs `runtime/docs/S14.md`):
- `.weaver/build_mpr_extras.cmd` — lift + build the game libraries into `work/lift_extras`, `work/build/mpr_extras` (private copy; uses the current `main.sites`); `.weaver/build_extras.cmd` — build mpr.exe from `runtime-wt/extras` against them (`game-build/build/extras`).
- `.weaver/boot_extras.sh [boot.py args]` — boot.py against that build, run folder `work/run_extras`. `--env NXRT_HDR_MODE=on`, `NXRT_UPSCALE_MODE=fsr1`, `NXRT_UPSCALE_SCENE_SCALE=60`, `NXRT_LATENCY_MODE=on`, `NXRT_GFX_LOG_FPS=1`, `NXRT_NVN_TRACE_SEC=90` (trace the frame N s after the first draw). HDR runs write `shot_<n>.hdrmap.png` and `.pfm` next to the screenshot.
- `.weaver/lat_ab.py LABEL [--toggle 8]` — latency A/B in one window-mode run (mode flipped every N s); `.weaver/lat_measure.py` — one run per state; `.weaver/fsr_matrix.py` — window 3840x2160 frame rate and present-pass GPU time for native / bilinear / FSR 1 / scene-scale variants with screenshots; `.weaver/s14_oracles.sh` — HDR off/on, window auto, Reflex runs with validation into `work/shots_s14`.
- `.weaver/spv_scan3d.py` — list fragment SPIR-V in the shader cache that sample 3D images. `work/ffx114/build.cmd` — build `amd_fidelityfx_vk.dll` from FidelityFX SDK v1.1.4 (MIT).

S17 (button prompts, branch prompts; docs `runtime/docs/S17.md`):
- `.weaver/boot_prompts.sh [boot.py args]` — boot.py against the prompts runtime worktree (build `game-build/build/prompts`, run dir `work/run_prompts`); `.weaver/trace_press_a.sh [tries]` — retries a traced title frame until the PRESS A text is lit (snaps of draws 40..142 in work/run_prompts).
- `.weaver/prompts_tests.ps1 [-Filter "play_|prompt_|..."] [-NoBuild]` — build + ctest of the prompts worktree. `.weaver/txtr_bc7_dump.py <TXTR> <png> [gob_height]` — decode a 1-mip block-linear BC7 TXTR; `.weaver/gob_rule_diff.py` — count TXTRs where the two block-height rules differ.

S4f (rendering fidelity) tools:
- `.weaver/bnrun.sh <seconds> [boot args]` — build the private game build (`game-build-nvn3`, runtime worktree `runtime-wt/nvn3`) and run it scripted into the game (`nrun.sh` without the build); env `PRESS` (button script), `SHOT_AT`/`SHOT_EVERY`. Results in `work/run_nvn3`. One-time configure: `cfg_nvn3.cmd`; `boot_nvn3.sh` is boot.py against that build.
- Run options (env, all `[nvn]` keys): `NXRT_NVN_SHOT_FRAMES=a:b:step,n` writes numbered PNGs of presented frames to `shots/`; `NXRT_NVN_TRACE_FRAME=n[,m]` traces frames (draws, uniforms, textures with sampler/view/memory, viewport, indexed vertex data); `NXRT_NVN_TRACE_DUMP_TEX=dir` writes the prepared and the GPU data of sampled textures; `NXRT_NVN_TRACE_TEX_EVENTS=1` logs the life of 128x128 cube textures.
- `.weaver/align_frames.py A_DIR B_DIR OUT_DIR [--amin N --bmin N --bmax M]` — match our screenshots to the best Eden frames (monotonic), side-by-side PNGs and ssim/mae table (`align.tsv`).
- `.weaver/bc6view.py t<id> out.png [level]` — decode a texture written by `trace_dump_tex` (BC6H cube or array) to a picture (needs `texture2ddecoder` in tools\.venv).
- `.weaver/wt_build.cmd <worktree>` configures and builds `nxrt_tests` of a runtime worktree; `.weaver/wt_target.cmd <worktree> <target>` builds one target (`nxrt_gfx_tests` holds the gfx test groups).
