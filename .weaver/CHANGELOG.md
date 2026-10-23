# Changelog
- S26: the scripted route goes from New Game through the hangar force fields, the walkway, the corridor door, the Air Lock (scan puzzle) and the Deck Alpha Access Hall to the Emergency Evacuation Area, where it stops (fire and a lip at the hill); new script steps @rays, @probe, @peek, @poke; room graph of the whole Frigate; morph ball speed measured (real, not explained).

- S22: all shipped binaries use the static Visual C++ runtime (no redistributable needed, the release builder checks imports); the ASTC texture test builds its own reference; settings and keyboard beam/visor keys documented and checked in the game; physics at 60/120/144/240 measured (walk, jump and ball match; one 240 Hz jump stall found, cause open).
- Phases 3-8: the real game boots, renders the title and plays into the Frigate Orpheon; movies, audio, window/controllers/keyboard and mouse, real-time timestep, display options, perf fixes, HDR and Reflex merged; setup tool and release builder done; repos made public.

- Phases 1 and 2: recompiler, runtime (ABI v2, C++ exceptions, graphics shell), offline graphics tools and MPR knowledge base built and verified; the dump passed every gate check (1.0.0, symbols present, 100% lifter coverage); GitHub repos created (private).

- Phase 0: build, analysis, debug and graphics toolchain installed and verified; reference projects cloned; project repos and records set up. Nothing game-specific yet.
