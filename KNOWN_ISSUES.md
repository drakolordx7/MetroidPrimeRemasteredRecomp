# Known issues

This list matches the latest release. The release notes of each version say what changed. If something here happens differently on your PC, or you hit a problem that is not listed, open an issue and attach `mpr.log`.

## Playing

- Only the start of the game has been played by hand: New Game, the Frigate Orpheon, and the first part of Tallon IV up to the Chozo Ruins' Main Plaza. An automated check loads all 275 areas, but nobody has played the later ones, so a story blocker could still be there.
- Some wall monitors on the Frigate show static instead of their screen graphics.
- With a controller, looking up and down with the right stick does not work yet (left and right does).
- Two rare crashes were seen in room-loading sweeps (a Magmoor Caverns area, and the Frigate air lock) and did not repeat.
- A few hundred of the game's shader programs, among them some gun shaders, have no translated stage and are skipped. What that looks like in play is not known.

## Hardware and setup

- Tested on one PC: an NVIDIA GeForce RTX 3080 on Windows 11. AMD and Intel GPUs have not been tried.
- Not tested with a physical controller (only through SDL's virtual gamepad), on a real HDR display, in exclusive fullscreen on a real display (the game falls back to borderless when Windows refuses it), or with Alt+Tab and mouse capture on a real display.
- After a graphics driver update, shaders have to be prepared again (launcher, Extras tab) or the first minutes of play stutter.
- XCI, NSZ and XCZ dumps are read by code that has only been tested on test files built for the project. No real cartridge dump or real compressed dump has been tested.
- Only the original version 1.0.0 base game works. Updates and patches are refused.
- Windows limits a file's full path to 260 characters. Keep the game folder path under about 180 characters.

## Not there yet

- Upscalers (FSR, DLSS, XeSS) are not there yet. AMD Anti-Lag 2 is written but has never been run on an AMD GPU.
- Windows 7, 8 and 8.1, 32-bit Windows, Linux and macOS.
