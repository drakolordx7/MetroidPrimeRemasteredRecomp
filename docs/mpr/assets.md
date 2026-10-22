# MPR assets: what the runtime has to read

Sources: `refs/retrotool` (`lib/src/format/*.rs`), `refs/PrimeRemasterStructs/*.bt`, the importers in `refs/MetroidPrimePort/platform/port_remastered_*.cpp`, and a header-only census of the real 1.0.0 RomFS (`tools/analysis/pak_census.py`, run on `game/romfs`; it reads PACK/TOCC/ADIR headers and TXTR HEAD chunks and nothing else). Tags: **[R]** retrotool, **[T]** the .bt templates, **[P]** the port's importers, **[C]** census of the real dump, **[B]** binary. Per-source detail with line pointers is in the working notes `work/kb/notes/{retrotool,bt_a,bt_b,port_assets}.md` (not committed).

## 1. Container

Everything is little-endian RFRM. [R] `rfrm.rs:16`, [T] `Run.bt`.

| Item | Layout | Evidence |
|---|---|---|
| RFRM form header | 32 B: `RFRM`, size u64 (payload only), u64 unknown, form id FourCC, reader version u32, writer version u32 | [R] [C] all 340 paks parse |
| Chunk header | 24 B: id, size u64, unk u32, skip u64; payload starts at +24+skip | [R] [C] |
| PAK | `RFRM/PACK` at 0, `RFRM/TOCC` at +32 containing `ADIR`, `META`, `STRG`; asset bodies follow at absolute offsets | [R] `pack.rs` [C] |
| ADIR entry | 52 B: type FourCC, UUID 16, reader u32, writer u32, offset u64, decompressed size u64, stored size u64; sorted by UUID | [R] [C] counts below |
| Compression | When stored size differs from decompressed size the stored bytes start with a u32 mode: 0 stored, 1/2/3 LZSS with 1/2/4-byte groups. First four bytes all zero means raw. No zstd/lz4/Oodle anywhere | [R] `compression.rs`, `lzss.rs` [P] |
| Per-asset footer | `FOOT` form with `AINF` is added by retrotool, it is not in the game files | [R] `foot.rs` |

The dump: 340 paks plus one loose file (`romfs/MaterialArchive.arc`, see 4). Layout is `Preload/{MPR1,MPRT}`, `UI/MPR1`, `Worlds/FrontEnd`, `Worlds/MP1/!<World>_Master` and per-room paks. [C]

## 2. Asset types in the dump [C]

340 paks, every ADIR entry counted. "Compressed" = entries whose stored size differs from the decompressed size (container level; textures, models and sound are uncompressed at this level and compressed inside).

| Type | Count | Stored MB | Reader/writer | What it is | Runtime? |
|---|---:|---:|---|---|---|
| TXTR | 7037 | 3636 | 47/51 | textures | yes, decode or upload |
| CMDL | 10163 | 1960 | 114/125 | static models | yes |
| CSMP | 1831 | 467 | 31/31 | audio sample | yes |
| FMV0 | 25 | 332 | 7/7 | movie | yes |
| MTRL | 778 | 285 | 168/168 | material archive, zlib inside | yes (materials, shaders) |
| SMDL | 421 | 248 | 127/133 | skinned models | yes |
| CHPR | 279 | 84 | 96/98 | character / skeleton / animation set | yes |
| LTPB | 280 | 83 | 66/73 | light probe bundles | yes |
| ROOM | 326 | 62 | 147/160 | level data (scripts, layers, docks) | yes |
| CLSN, DCLN | 275, 240 | 18, 1.2 | 11/22, 9/18 | collision trees | yes |
| WMDL | 75 | 9 | 118/124 | liquid surface models | yes |
| GENP, SWSH, DPSM, ELSM, ELC2, WPSM, CRSM, VECF | 1437, 60, 33, 10, 26, 53, 46, 2 | 8 | v61/62 etc. | particle, swoosh, electric, weapon, collision-response, vector-field definitions | yes |
| MSBT | 30 | 7 | 10/10 | text (7 languages) | yes |
| SVGM | 89 | 4.5 | 3/3 | unidentified, 89 of 89 compressed | unknown |
| MCON, LPTH | 587, 276 | 3.5, 1.4 | 41/44, 7/7 | visual data, paths | yes |
| CAUD, CBNK, CMID, CABH | 2470, 11, 4, 2 | 1.2 | 31/31 etc. | audio events, banks, MIDI, bus hierarchy | yes |
| CMAP, GUIF, FONT, MATI, REFL, LSCN, ENUM, DGRP, LFSM, FSMC, LDTA, UINF, SHNT, LUHR, LMPU | various | under 3 | | map frames, HUD frames, fonts, material instances, reflection probes, scene, enums, dependency groups, state machines, tweak data, universe info, shader hint | yes |

No `GFXL` (Scaleform) assets exist in the dump, so menus are GUIF frames or something carried in the unidentified SVGM; `CScaleformFlashLibrary.bt` describes a type that this build does not use.

## 3. TXTR [R] [T] [P] [C]

- Form `TXTR` v47/51. `HEAD` chunk: kind u32, format u32, width, height, layers, `tile_mode`, `swizzle`, mip count, mip sizes, 10-byte sampler block. `META` lists the read regions and destination buffers; texels are reassembled from them (each buffer LZSS or stored). [R] `txtr.rs:109-171`
- In the dump every texture has `tile_mode = 0` and `swizzle = 0` (7037 of 7037). [C] Both fields are read by every importer and ignored; the data is Tegra block-linear with the block height inferred from the dimensions (GOB 64x8 B, heights 16/8/4/2/1 by size). [R] `txtr.rs:529`, [P] `port_remastered_tegra_swizzle.cpp`.
- Kinds in use: 1 = 2D, 2 = 3D, 3 = cube, 5 = 2D array. [C] 4/8/6/7 not present.
- Format enum (retrotool numbering) and what the dump uses [C]; ASTC is the bulk of the data:

| Code | Format | Textures | Stored MB |
|---|---|---:|---:|
| 54 | ASTC 5x4 | 1079 | 875 |
| 82 | BC6H SFLOAT (2D array; plus 7 others) | 280 | 803 |
| 69 | ASTC 5x5 sRGB | 785 + 26 | 487 + 7 |
| 58 | ASTC 8x5 | 1083 + 3 + 2 | 447 + 1.4 + 0.3 |
| 84 | BC7 sRGB | 891 + 28 | 362 + 25 |
| 72 | ASTC 8x5 sRGB | 1392 + 26 + 5 | 294 + 24 + 1 |
| 81 | BC6H UFLOAT (cube maps, kind 3) | 1005 + 12 | 135 + 48 |
| 13, 12 | RGBA8 sRGB, RGBA8 | 89, 91 | 45, 24 |
| 83 | BC7 | 163 + 4 | 26 + 6 |
| 28, 26 | BC5, BC4 | 32, 6 | 7, 2 |
| 0, 55, 21, 23 | R8, ASTC 5x5, BC1 sRGB, BC2 sRGB | small | small |

So four ASTC footprints (5x4, 5x5, 8x5 and their sRGB variants) carry about 2.1 GB of 3.6 GB. ASTC to BC7 offline (plan decision) needs a 5x4/5x5/8x5 decoder plus a BC7 encoder; the NVIDIA ASTC hardware path is not an option on desktop. BC6H cube/array maps and BC7 can be uploaded as is (Vulkan `BC6H_SFLOAT_BLOCK`, `BC7_*`). [C]
- Only the top mip of layer 0 is decoded by the port; sRGB is flagged but not applied in its 2D path. [P] Not relevant to us, but it shows the format fields are reliable.
- Anomaly: retrotool reports 64 and 128 bytes per pixel for RGBA16/RGBA32 formats (should be 8 and 16). Not present in the dump.

## 4. Materials and shaders

- `MTRL` form v168 (per-pak) is `META` + a zlib stream (first bytes `78 DA` at +32 in the sample inspected). Contents are not parsed by retrotool. [R] `mtrl.rs:40-46` [C]
- The loose `romfs/MaterialArchive.arc` is an `RFRM/MTRL` v22 file, 3.4 MB, whose first chunk is tagged `SDX ` (about 1.8 MB). v22 is the version `MaterialArchive.bt` is active for. [C] [T] `Run.bt:53-55`
- `MaterialArchive.bt` describes: per-material `SMaterialTOCEntry` with a list of `SShaderTOCEntry` identified by technique letter (`x` none, `z` depth only, `g` deferred G-buffer, `i` deferred instance, `f` forward, `s`/`w`/`m` particle sprite/swoosh/model) plus a 16-byte permutation, `SShaderImportDesc` (program indices for vertex, pixel, geometry, compute), a feature set with boolean expressions, graphics state, and the `SShaderSource` blob: `state u8, strLen u32, str, dataLen u32, data[dataLen]`. [T] `MaterialArchive.bt:14-54`
- What the blob is (GLSL text, SPIR-V, NVN/Maxwell binary) is not established by any source. The binary names the loaders: `CGraphicsClient::LoadMaterialArchive` 0x7766d8 / 0x7767a0, `CMaterialExec::CMaterialImporter::Exec` 0x134ad8, `NMaterialArchive::SShaderSource::SShaderSource` 0x17d4e4, `NMaterialArchive::SArchiveMetaData` 0x17d3d8. Decompiling `SShaderSource` and its consumer answers it. [B] This is open work for S4.
- `CMDL` materials list `shader_id` UUIDs that are never resolved by retrotool. [R] `cmdl.rs:365`

## 5. Models, characters, effects

- CMDL v114/125, SMDL v127/133, WMDL v118/124: chunks `HEAD/SKHD/WDHD`, `MTRL`, `MESH`, `VBUF`, `IBUF`, `GPU`, `META`. Vertex formats are a 41-entry enum (R8 UNORM ... RGBA32 FLOAT), components 0 to 28 (position, normal, tangents, 4 UVs, colour, bone indices/weights, baked lighting, instance data, material choice). GPU buffers are LZSS-compressed per `META` entry. [R] `cmdl.rs`
- CHPR (characters) mixes skeleton and animation streams; the compressed animation stream semantics are not in the templates. The port documents the dequantisation ops it implements (`NAnimComp::init_dequant_real32` 0xbb7bf0, `init_dequant_int32` 0xbb7e90, `NAnimOp::dquant_bits` 0xba2de0, `tween_real32` 0xba35d0). [P] `port_remastered_anim.cpp`
- Particle and effect assets (GENP and friends, v61/62) are element-graph programs evaluated at runtime; the port's `PortParticleMath.hpp` lists the matching MPR functions (`CCEGradient::GetValue` 0x2c8d48, `CVERandomVector::GetValue` 0x29e954, `DistanceFromCameraBlend::CalculateBlendValue` 0x298f44 ...), all validated in `symbols.json`.

## 6. Movies [C] [P]

`FMV0` (25 assets, 332 MB). The payload after the 32-byte RFRM header is a plain MP4 (`ftyp mp42/mp41`). The first movie's `stsd` holds `avc1` with `avcC` profile 0x4d (Main), level 0x2a (4.2), 1600x900; no `mp4a` box appears in that file, so the video track is video-only. The port assumes 1600x900 at 60 fps and does not check the codec. The binary imports 41 `movie::` functions from `subsdk0` (Nintendo multimedia, also carrying mkv, FDK-AAC and Opus support). Media Foundation or FFmpeg can decode the H.264 payload. Movie audio is not in the MP4 and its source is still unknown.

## 7. Audio

- `CSMP` (1831 samples, 467 MB, v31): chunks `FMTA` then `DATA`. In the sample inspected `FMTA` is 5 bytes and the `DATA` chunk opens with a small header that contains 48000 (0xBB80); the codec is not identified. Candidates are PCM16 or Nintendo ADPCM (DSPADPCM) or Opus, given the decoders in `subsdk0`. The binary talks to `nn::audio` (renderer, voices, submix, reverb, delay, aux, I3dl2), so the runtime needs an `nn::audio` audio-renderer implementation either way. [C] [B]
- `CAUD` (2470): sound effect definitions with a name string (for example `16_Furnaces Ember Loop`), volume and pitch floats and referenced sample UUIDs. `CBNK` (banks), `CMID` (MIDI), `CABH` (bus hierarchy). Layouts: `CAudio*.bt`. [T]
- Nothing in `retrotool` or the port decodes MPR audio.

## 8. Text, UI, fonts

- `MSBT` v10: seven language chunks (EUFR, USFR, EUSP, USSP, EUGE, EUIT, EUDU), each a Nintendo `MsgStdBn` file (UTF-16LE, `LBL1` and `TXT2` sections); label format `[XXXXXXXX]_n`. Remastered inline tags: 0x0E start, 0x0F end, colour group 0 type 3. [P] `port_remastered_text.cpp`
- `FONT` v18 (3 fonts): glyph record 44 bytes, distance-field atlases (red channel), kerning pairs. [P] `port_remastered_font.cpp`
- `GUIF` v17 (14 frames) are the HUD frames; `CMAP` (7) map frames. Header-only evidence of widget names (`headwidget_xrayscope`) in the first GUIF inspected. [C]

## 9. Open items to settle on the dump

1. Shader blob format in `SShaderSource.data` and the `SDX ` chunk of `MaterialArchive.arc`.
2. CSMP codec; where movie audio lives.
3. Identity of `SVGM` (89 compressed assets, all in world masters).
4. Whether the 14 `ETextureFormat` ASTC footprints in the enum beyond 5x4/5x5/8x5 are ever used (no: not in this build).
5. Retrotool's `skip` field and the `unk` words in RFRM/chunk headers.
