# Known issues

The port is early. It runs from the title screen into the first level (the Frigate Orpheon) and is not playable from start to finish. This page lists what we already know is wrong, so you do not need to report it again. If you have a new bug, use the issue forms and attach `mpr.log`. If one of these happens differently on your machine, a screenshot and your GPU and driver version still help.

Links go to the nxrecomp repository, where the development logs live.

## Visual bugs

- **Rainbow textures.** Some surfaces show wrong colours, like a rainbow or noise. The cause is not found yet. Textures are converted from the Switch's ASTC format to BC7 during setup, so that step is one place to look. Tell us where you see it. See [tools/setup](https://github.com/drakolordx7/nxrecomp/blob/main/tools/setup/README.md) for how textures are converted.
- **Black textures.** Some surfaces and objects draw black. The [NVN correctness log](https://github.com/drakolordx7/nxrecomp/blob/main/runtime/docs/S4e.md) describes how earlier black-world bugs were traced.
- **Misaligned effects.** Some effects are drawn offset from the thing they belong to.
- **A broken character model.** At least one character model draws distorted.
- **Static on the Frigate hangar door.** A rectangle of noise covers the door in the hangar.
- **Dark arm cannon and gunship.** Samus's arm cannon is drawn unlit, and the gunship is dark.
- **A black spike artefact** shows in some scenes.

The graphics layer (NVN on Vulkan) still lacks a few things the game calls: sparse virtual textures are treated as fully resident, transform feedback is recorded but not run, occlusion counters always report "visible", and integer vertex attributes are converted to floats. We have not tied any of the bugs above to these. The full list is under [Open points](https://github.com/drakolordx7/nxrecomp/blob/main/runtime/docs/S4d.md#open-points).

## Performance

- **Stutter and low frame rate in gameplay.** The title screen holds 140 fps with a 144 fps cap. Gameplay is slower and stutters. The game records the pipelines it builds and prebuilds them on the next run, so the second run should hitch less than the first. Keep `pipeline_cache.bin` and `pipeline_keys.bin` next to `mpr.exe`. Background: [display options and frame-time performance](https://github.com/drakolordx7/nxrecomp/blob/main/runtime/docs/S10.md).

## Audio

- **No sound on some setups.** Sound plays through XAudio2 on your default output device. It has not been heard on every machine yet. If you get silence, look in `mpr.log` for the list of output devices, then set `[audio] device` in `mpr.ini` to part of the name of the one you use. Say what output you have when you report it. The keys and the `wav_dump` option (writes the game's sound to a file, so we can tell whether the game or the device is silent) are in the [audio notes](https://github.com/drakolordx7/nxrecomp/blob/main/runtime/docs/CONFIG.md#audio-notes).

## Gameplay and PC features

- **Only the start of the game has been run.** Later areas, saving and loading, and the rest of the cutscenes are not checked yet.
- **High refresh rates are not verified in gameplay.** Movies and menus run at real speed at 60, 120, 144 and 240 Hz. Walking, jumping, morph ball friction, projectile range and the HUD timer still need checking at high rates. If something feels wrong, set `[time] mode = fixed` (the 60 Hz lock) and tell us what changed. See the [high refresh log](https://github.com/drakolordx7/nxrecomp/blob/main/runtime/docs/S11.md).
- **Mouse aim and controls are unchecked in real gameplay.** That covers mouse aim, context detection, the Switch button layout and beam and visor combinations. The morph ball mouse camera and free look with the mouse are not done. Above 60 fps, mouse aim moves in steps at the game's tick rate. See [play mode](https://github.com/drakolordx7/nxrecomp/blob/main/runtime/docs/S8.md).
- **HDR, FSR 3.1, DLSS, XeSS, Reflex and Anti-Lag 2 are not in a release yet.**

## Setup and release

- Only the original v1.0.0 base game works. Updates and patches are refused.
- Windows 10 and 11 on x64 with a Vulkan 1.3 GPU. Nothing else is planned.

## For developers

- Licence texts are missing from the release package for Eden and yuzu (GPL-2.0), libc++abi and the MSVC runtime.
- RGBA8 and BC5 entries in the texture cache are still to be dealt with in the release build.
- When no shader folder is configured, the runtime falls back to a development path as well as `./shader_cache/spirv`.
- The `gfx_nvn_scene_stress` test failed once under heavy load and passed when run alone. If it fails for you, rerun it on its own and tell us.
