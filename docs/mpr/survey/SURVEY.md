# MPR asset survey (S4c)

Measured on the v1.0.0 dump, 2026-10-21. Machine: i9-12900K (16C/24T), shared with other heavy jobs during the runs, so
timings are conservative. Everything extracted lives under `work/survey/` (not in git); scripts are in `tools/survey/`
(tools repo). Run order is at the end.

## Summary

| Question | Answer |
|---|---|
| Shaders | Real NVN (GLSLC) program sets, zlib-wrapped, not only in `MaterialArchive.arc`: 583 sets there plus 46,936 sets inside the 767 pak `MTRL` assets. 67,506 distinct code blocks (33,744 vertex, 33,744 pixel, 12 geometry, 6 compute). The tools/shaders harness reads them unchanged. |
| Translator | Ryujinx (the Wonder harness in tools/shaders). 9,164 of 9,164 blocks pass spirv-val (100%) against smo's 3,776 (41.2%); smo never wins a block. |
| Textures | 6,927 distinct TXTR. 4,369 ASTC (4 footprints: 5x4, 5x5, 8x5, plus sRGB twins), 2,327 BCn/BC6H/BC7 (pass through), 231 uncompressed. 4,350 MPix of ASTC to convert (all mips), 2.83 GB ASTC -> about 4.35 GB BC7. Estimated first-run conversion about 12 min if parallel across textures, about 23 min if parallel per level (quality 5). |
| Audio | Every CSMP is Nintendo DSP-ADPCM, played through `nn::audio` AudioRenderer (`ParseAdpcmHeader`, `AcquireVoiceSlot`), driven by Retro's own `CAxal*` engine. No Opus, no middleware. |
| Movies | 25 FMV0 = plain MP4, H.264 Main L4.2, 1600x900, 60 fps, 7 of them with one AAC-LC 5.1 track. All 25 decode through Windows Media Foundation (tested). |
| UI | 14 GUIF frames, 0 Scaleform/GFXL anywhere. The front end is a 3D "world" (`UI_FrontEnd.pak`), not flash. |
| Inventory | 340 paks (6.8 GB), 31,714 directory entries, 31,602 distinct assets, 43 asset types. |

## 1. Inventory

`python tools/survey/inventory.py` (reads only the PACK/TOCC/ADIR directory of each pak). Sizes in MB. "Stored" equals
"decompressed" at the directory level for almost everything because the compression is inside the asset (TXTR buffers are
LZSS, MTRL bodies zlib).

| Type | Entries | Distinct | MB | What |
|---|---:|---:|---:|---|
| TXTR | 7,037 | 6,973 | 3,636 | textures (5,197 MB after LZSS) |
| CMDL | 10,163 | 10,147 | 1,960 | static models |
| CSMP | 1,831 | 1,831 | 467 | audio samples (DSP-ADPCM) |
| FMV0 | 25 | 25 | 332 | movies (MP4) |
| MTRL | 778 | 777 | 285 | material archives with embedded shaders |
| SMDL | 421 | 421 | 248 | skinned models |
| CHPR / LTPB / ROOM | 279 / 280 / 326 | | 84 / 83 / 62 | characters, light probes, rooms |
| CLSN, WMDL, GENP, MSBT, SVGM, MCON | | | 18, 9, 7.5, 7.3, 4.5, 3.5 | collision, world models, particles, text, ... |
| CAUD | 2,470 | 2,453 | 1.2 | sound-effect definitions (reference CSMP) |
| GUIF | 14 | 14 | 0.1 | HUD / menu frames |
| 25 more types | | | < 1 each | MATI 2,809, REFL 993, LSCN 848, LPTH 276, DCLN 240, CBNK 11, CABH 2, CMID 4, ... |
| Total | 31,714 | 31,602 | 7,215 | |

By folder: `Worlds/MP1` 286 paks / 4.58 GB (23,556 assets), `Preload` 12 / 1.94 GB (`DuplicateData.pak` alone is 1.62 GB),
`Worlds/FrontEnd` 38 / 0.57 GB, `UI` 1 / 0.11 GB, three small root paks. Full table: `work/survey/inventory.json`.

Note: `retrotool pak extract` stops on one asset name containing `?` (`gun_cskr_DGRP?`, `Preload/MPR1/SamusGunMP1.pak`); that pak
is extracted only partly (14 of 29 files). It does not affect the numbers above, which come from the directory.

## 2. Shaders

### Where and what format

- `romfs/MaterialArchive.arc` is an RFRM `MTRL` (reader version 22) with two backends: `SDX` (1,168 records of DXBC, the PC D3D path,
  unused on Switch) and `SNVN` (583 records, NVN). `SNVN` holds a 22 KB table of contents (61 materials, e.g. `UberPostMP1`, `Tonemap`,
  `Bloom`, `SSAO`, `FXAA`, `VolumetricFog_*`, `LightPrePass`, `WaterSim`; 583 shader entries, one per record) followed by the
  program records.
- Every one of the 767 pak `MTRL` assets (reader version 168, 285 MB; zlib body named by the META footer chunk, decompressing to an
  `EXPT` blob, 352 MB in total) embeds the same kind of record: 46,936 program sets, always a vertex + pixel pair.
  This is where the world/model shaders are. (An earlier assumption was that only the arc held shaders. The pak copies hold 80x more.)
- One record = `u8 0, u32 N (flags in the high bits), u32 kind (0x11 = VS+PS, 0x19 = VS+GS+PS, 0x08 = compute), u32 zlibLen, zlib`,
  then a small trailer (stage count, offsets, control size). The zlib output is exactly NVN's GLSLC program layout, the same as
  Wonder's BNSH payloads: per stage a code block (starts `78 56 34 12`, or `79 56 34 12` for compute; 0x30-byte NVN header, then the
  0x50-byte SPH at +0x30, then Maxwell code, 0x100-aligned), followed by one control section per stage (magic `34 12 76 98`;
  +0x6f8 program length, +0x6fc/+0x700 constant-data size/offset, +0x704 code block size, +0x708 start 0x30, +0x714 stage).
  Control sections are 0x880 bytes in 75,180 of 95,044 stages, and 0x890 (9,571), 0x950 (9,568), 0x88c (481), 0x94c (240) or 0x940 (4) in the rest, so a parser must find them by magic.
- Header snippet (first block of arc record 0, a pixel shader): `78 56 34 12 00 ... (0x30 bytes)`, SPH `62 54 06 00 ...`, control `34 12 76 98 01 00 00 00 10 00 00 00 20 01 00 00 0b 00 00 00 78 08 00 00`.
- No format conversion is needed: `tools/survey/extract_shaders.py` only cuts the sets apart and writes the harness corpus layout
  (`manifest.tsv`, `code_<hash>.bin`, `ctrl_<hash>.bin`). Pak and arc blocks do not overlap (0 shared).

### Counts

| | Arc | Pak MTRL | Total distinct |
|---|---:|---:|---:|
| program sets | 583 | 46,936 | 47,519 |
| distinct code+control blocks | 1,164 | 66,342 | 67,506 |
| vertex / pixel / geometry / compute | 573 / 573 / 12 / 6 | 33,171 / 33,171 / 0 / 0 | 33,744 / 33,744 / 12 / 6 |

Stage mix per arc set: 565 VS+PS, 12 VS+GS+PS, 6 compute. Median program 848 bytes, largest 14 KB in the arc.

### Translator comparison (spirv-val, `--target-env vulkan1.3`, independent re-validation)

Corpus: all 1,164 arc blocks plus a seeded random sample of 8,000 of the 66,342 pak blocks (9,164 distinct blocks, 13.6% of everything;
`sample_corpus.py`, seed 1). Both translators were run through the locked `tools/shaders/oracle/run_oracle.py` (282 s). The full 67,506-block
run was started and stopped because the machine was loaded; the Ryujinx harness alone is about 16 blocks/s under that load.

| translator | blocks | translated | spirv-val pass | rate |
|---|---:|---:|---:|---:|
| Ryujinx harness | 9,164 | 9,164 | 9,164 | 100% (5,647 first try, 3,517 after the DebugMode retry) |
| smo `mx_translate` | 9,164 | 3,776 | 3,776 | 41.2% |

| stage | blocks | Ryujinx pass | smo pass |
|---|---:|---:|---:|
| vertex | 4,509 | 4,509 | 3,607 |
| pixel | 4,637 | 4,637 | 157 |
| geometry | 12 | 12 | 8 |
| compute | 6 | 6 | 4 |

Arc only (1,164 blocks): Ryujinx 1,164 (1,066 first try, 98 retry), smo 700 (60.1%). Blocks passing in both: 3,776; only Ryujinx: 5,388; only smo: 0; neither: 0.
smo failures: PIXLD 4,480, indexed attribute load (ALD.indexed) 832, TEX 65, SUST 6, attribute store 4, TLD 1.
Ryujinx retries: 3,042 `AstOperation` to `AstOperand` cast, 467 `KeyNotFoundException` in the SPIR-V call/code generator, 8 texture-operation cast (the
failure class Wonder documents; the harness retries with DebugMode).

### Findings that matter for S4

- PIXLD.MY_INDEX is not implemented by Ryujinx (453 of 573 arc pixel shaders, and 4,480 of 4,637 pixel shaders in the sample, 97%; warning "Pixld is not implemented"). The result
  register is simply not written. The shaders that use it start with an epilogue that reads the pixel position, a byte table at
  `c[0] + 0x620` and masks at `c[0] + 0x630` (probably the driver's alpha-to-coverage dither, inferred, not verified). Output stays valid
  SPIR-V and the visible colour path was unchanged in the 40 shaders inspected as GLSL. The runtime must either supply that
  `c[0]` data or neutralise the epilogue; a small Ryujinx patch (PIXLD.MY_INDEX -> `gl_SampleID`/0) would remove the warning.
- smo's translator stops at PIXLD, indexed attribute loads (832 pak blocks), TEX (65), SUST, an attribute store and TLD. It never beat Ryujinx on any block, and with PIXLD fixed it would still lose 900+ blocks.
- 38% of the sample (3,517 blocks; 8% of arc blocks) need the harness's DebugMode retry (Ryujinx expression-propagation exception); no block fails. S4 should ship the translated SPIR-V rather than translate on the player's machine, and may want the retry's lost optimisation fixed upstream.
- 4 geometry shaders write `ViewportMask` (attribute 0x3A0), which Ryujinx reports as unsupported for the geometry stage on the host profile.
- Resource shape (arc, Ryujinx results): user uniform buffers are NVN `c3..c6`, `c1` is the compiler-hoisted constant data (428 blocks),
  `c0` driver constants (30 blocks plus the epilogue above); 1,469 2D texture bindings, 241 3D, 149 cube, 16 multisample, shadow samplers
  and 6 image bindings. 648 blocks ask for the draw-time `coordNormalized` query.

## 3. Textures

Parser: `txtr_tally.py` (header + META footer only). Distinct = by asset id, 6,927 of 6,984 extracted files (pak copies removed).

| Format family | Textures | MPix mip0 | MPix all mips | GPU MB |
|---|---:|---:|---:|---:|
| ASTC linear (5x4 1,073; 8x5 1,081; 5x5 10) | 2,164 | 1,792 | 2,390 | 1,572 |
| ASTC sRGB (5x5 812; 8x5 1,393) | 2,205 | 1,474 | 1,961 | 1,257 |
| BC6H (BptcUfloat 1,017, BptcSfloat 287) | 1,304 | 1,182 | 1,231 | 1,499 |
| BC7 (BptcUnorm 167, sRGB 855) | 1,022 | 582 | 651 | 715 |
| BC1/2/4/5 (Bc5 32, Bc4 6, Bc1 and Bc2 sRGB 2 each) | 42 | 12 | 16 | 12 |
| RGBA8 (sRGB 87, linear 91) and R8 12 | 190 | 38 | 40 | 143 |
| Total | 6,927 | | | 5,197 |

- Kinds: 2D 5,493, Cube 1,020, 2DArray 367, 3D 47. ASTC: 4,305 plain 2D, 53 arrays (3 to 192 layers), 10 cubes, 2 volume textures (64x64x64,
  ASTC 8x5 slices; the others are 45 RGBA8 33x33x33 colour-grading LUTs). BC6H is nearly all cubemaps (1,010) and 4-layer arrays.
- Sizes: 1024^2 2,046, 128^2 1,304, 512^2 1,140, 256^2 505, 2048^2 154, plus 4096x2048. Mips 1 to 13. Header `tile_mode` and `swizzle` are 0 in every texture.
- LZSS buffer modes seen: 3 (almost all), 2, and raw (0).

### Tiling (tools/tiling vs the real GPU buffers)

`txtr_pipeline.py layout`: for 681 distinct (format, kind, size, layers, mips) combinations covering all 6,927 textures,
`tegra_tile` computes a tiled size equal to the TXTR's GPU buffer size, with the block height from the `tegra_swizzle`
rule (what retrotool uses). `tools/tiling`'s own `default_gob_blocks_y()` also matches 681/681. 3D: RGBA8 33^3 needs
`gob_y=1, gob_z=16` (`gob_y=2, gob_z=8` gives the same size but wrong bytes), and the allocation is the untrimmed layer stride; for
the ASTC 64^3 volumes every setting gives the same size (small), so use the same rule as the LUTs.

### End-to-end proof (`txtr_pipeline.py samples --n 5`, 56 textures, every format/kind present)

- LZSS decode -> `tegra_tile untile` -> size check: 56/56. Compared byte-for-byte with retrotool's (tegra_swizzle) output: 36/36 identical
  (all single-layer 2D samples: ASTC, BC1/2/4/5/6H/7, R8, RGBA8). Arrays, cubes and 3D have no retrotool reference output; their sizes match.
- ASTC -> BC7 with `astc2bc7` (quality 5, level 0, layer 0) on 35 samples (2D, cube, array; 5x4, 5x5, 5x5 sRGB, 8x5, 8x5 sRGB):
  PSNR RGB min 36.15 dB, mean 54.64 dB; SSIM(luma) min 0.9753, mean 0.9958. Per footprint mean: 5x4 50.1, 5x5 44.4, 5x5 sRGB 54.9, 8x5 57.3, 8x5 sRGB 60.5 dB.
  Worst cases are 1024-wide 5x5 and 5x4 content (36 to 37 dB). 14 of the samples carry real alpha; alpha is reproduced (PSNR RGBA min 35.9 dB).
  Reference is the ASTC decode (astcenc), BC7 decoded by the independent `bc7dec`.

### Conversion time

- ASTC to convert: 4,369 textures, 44,127 mip levels, layers and slices included, 4,350 MPix.
- Measured in-process throughput (astc2bc7 `--bench`, quality 5, real MPR blocks): 7.2 MPix/s at 2048^2, 4.8 at 1024^2, 4.1 at 512^2, 2.6 at 256^2, 1.2 at 128^2.
  Per-level threading with those rates gives 22.6 min for the whole set. Texture-level parallelism (one texture per thread, the README's
  measured about 6 MPix/s) gives about 12 min. Quality 3 is about 3x faster.
- The CLI run per level is not viable: 612 levels (60 textures, 67 MPix) took 70 s = 0.96 MPix/s, dominated by process start; the same
  would be about 75 min for everything. The setup tool must call the library in-process.
- Output size: BC7 is 1 byte per pixel, so about 4.35 GB of BC7 against 2.83 GB of ASTC (RGBA8 would be about 17 GB).
- Gaps: `astc2bc7` does not take mip chains, arrays or 3D in one call (handle per level/layer/slice; the 2 volume textures have 2D ASTC footprints, so per slice works).
  BC6H/BC7/BC1-5 need no conversion.

## 4. Audio

- 1,825 of 1,825 extracted CSMP: chunks `FMTA` (5 bytes: channel count, channel-layout mask) + `DATA`, 62 also carry `CRMS` (envelope) and 61 `RAS3` (seek table).
  `DATA` starts with a Nintendo DSP-ADPCM header (little-endian here): sample count, nibble count (consistent in 1,825/1,825), sample rate, loop flag, format, then 16 predictor coefficients at +0x1C
  (plausible values such as 1160, -629, 2831, ...), 14 samples per 8-byte frame (0.572 bytes/sample/channel). Channels: mono 1,685, stereo 131, 4ch 7, 5.1 2.
  Sample rates: 48,000 Hz for 1,699, 44,100 (39), 32,000 (71), 24,000 (13), 22,050 (2), one 4,000 Hz stub.
- CAUD (2,470) are sound-effect definitions that point at CSMP, CBNK (11) sample banks, CABH (2) bus hierarchy, CMID (4) sequences. No codec in them.
- Symbols (`audio_symbols.py`, main/sdk/subsdk0 `.dynsym`): `main` imports 127 `nn::audio` functions, all AudioRenderer (45 `AudioRenderer`, `AcquireVoiceSlot`, `AcquireSubMix`, `AcquireFinalMix`,
  `AddDeviceSink`, reverb/I3DL2/delay/aux/limiter effects, `ParseAdpcmHeader`), no AudioOut, no `nn::codec`, no Opus imports. `sdk` defines the audio renderer, AudioOut
  and `nn::codec`/Opus; `subsdk0` (the multimedia stack) uses AudioOut plus its own FDK-AAC, vorbis, mp3 and Opus. No FMOD, Wwise, CRI, Bink or XAudio symbols.
  Game classes: `CAudioManager` 193 methods, `CAxalSystem`, `CAxalVoice`, `NAxal::` (about 830 names), `CAudioSampler`, `CSoundGOC`, `NMP1AudioSounds` 1,003.
- Consequence: the host needs a DSP-ADPCM decoder and an AudioRenderer implementation (mix graph, voices, effects). Opus is not used by the game audio.

## 5. Movies

`movies.py` + `ffprobe 8.1.2`: all 25 FMV0 are an `RFRM FMV0` wrapper (MP4 starts at 0x20, `ftyp` first) around MP4, H.264 Main, level 4.2, 1600x900, 60 fps, yuv420p, BT.709 limited, B-frames
(reorder depth 1), about 10 Mbit/s, 1.0 to 30.0 s (sum 264 s, 332 MB). 7 movies have one AAC-LC audio track (6 channels, 48 kHz, about 700 kbit/s); the other 18 are silent (their
sound is presumably CSMP/streamed). 10 are in `UI/MPR1/UIMP1.pak` and 15 in `Worlds/FrontEnd`.

Media Foundation: Microsoft documents the H.264 MFT as Baseline/Main/High up to level 5.1, up to 4096x2304
([learn.microsoft.com H.264 video decoder](https://learn.microsoft.com/en-us/windows/win32/medfound/h-264-video-decoder)). Tested with `mf_decode_test.exe`
(IMFSourceReader, software path): 25/25 decode, 1600x900 at 60 fps, 91 to 128 fps decode speed including RGB32 conversion, and the 6-channel AAC decodes to 16-bit PCM
(7 files, durations match). Media Foundation is viable; FFmpeg fallback is not needed for these.

## 6. UI

- GUIF: 14, all in `Preload/MPR1/GuiSysMP1.pak`: `FRME_BaseHud`, `CombatHud`, `ScanHud`, `ScanHudFlat`, `XRayHudNew`, `ThermalHud`, `Helmet`, `BallHud`, `PauseScreen`,
  `PauseScreenInstructions`, `MapScreen`, `QuitScreen`, `MsgScreen`, `GenericMenu`. The same 14 `FRME_` names are the only ones in `main`'s strings.
- Scaleform/GFXL: none. No asset type, no SWF/GFX header in any of the 7.2 GB (30 raw hits of `GFX`/`CFX`/`FWS` were checked: random bytes), no Scaleform strings or symbols in `main.elf`.
  The earlier assumption that menus use Scaleform is wrong for this build.
- The front end (title, file select, options, extras) is `Worlds/FrontEnd` (38 paks, 570 MB: ROOM/CMDL/TXTR/CAUD/FMV0) driven by `CFrontEndManagerGOC` / `CFrontEndIOWin`, i.e. a 3D scene,
  and `UI/MPR1/UIMP1.pak` (112 MB, mostly textures and 10 movies). All UI is therefore GUIF + world rendering; no separate flash runtime is needed.

## Reproduce

```text
pwsh tools\survey\extract_all.ps1                       # all paks -> work\survey\paks (about 7 s)
tools\.venv\Scripts\python tools\survey\inventory.py
tools\.venv\Scripts\python tools\survey\extract_shaders.py game\romfs\MaterialArchive.arc --out work\survey\shaders\corpus --paks work\survey\paks
tools\.venv\Scripts\python tools\survey\sample_corpus.py work\survey\shaders\corpus --out work\survey\shaders\corpus_sample --n 8000
$env:VULKAN_SDK='C:\VulkanSDK\1.4.363.0'
tools\.venv\Scripts\python tools\shaders\oracle\run_oracle.py --corpus work\survey\shaders\corpus_sample --out work\survey\shaders\oracle_sample --jobs 20
tools\.venv\Scripts\python tools\survey\txtr_tally.py
tools\.venv\Scripts\python tools\survey\txtr_pipeline.py layout | samples --n 5 | bulk --count 60
python tools\survey\movies.py ; pwsh tools\survey\build_mf_test.ps1 ; work\survey\fmv\mf_decode_test.exe work\survey\fmv\*.mp4
python tools\survey\audio_symbols.py ; python tools\survey\ui_survey.py
```

Known gaps: the translator pass rates cover 9,164 of 67,506 distinct blocks (all arc blocks plus a seeded random sample). PIXLD semantics and the alpha-to-coverage reading are inferred, not verified against a capture.
