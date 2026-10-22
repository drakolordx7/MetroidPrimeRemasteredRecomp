# Hook candidates for the PC features

Ranked per feature. In a static recompilation a "hook" means one of three things: override the function by symbol, patch a call site, or replace an `nn::` import with a native implementation. All addresses are `main` offsets (equal to the vaddr in `work/elf/main.elf`; add the IDA image base for a VA).

Evidence tags: **[B]** confirmed on the real 1.0.0 main by `validate_kb.py` or a direct disassembly; **[M]** a mod in `refs/` hooks it (path in `frag/`); **[W]** a community patch for build ID 67C9CA14... touches it (`patches.json`); **[P]** MetroidPrimePort design notes (GameCube game, same engine lineage; ideas only). Anything not tagged [B] is a claim until validated.

Two corrections to the earlier assumptions, both found on the binary:

- `main` imports only `nn::hid::GetNpadState` (three overloads: FullKey, JoyDual, Handheld), not `GetNpadStates`, `GetKeyboardState` or `GetMouseState`. The mods hook `nn::hid::detail::GetNpadStates`, which lives in `sdk`. Input synthesis in the recompiler belongs at the `GetNpadState` import. [B]
- `NTonemap::build_tonemap_eval_params` exists as `_ZN8NTonemap25build_tonemap_eval_paramsERK14STonemapParams` (with the `K`). The practice mod's string is right. [B]

## 1. Raw mouse aim

How the retail code turns input into aim (read in IDA on the validated `main.elf`): `CPlayerMP1::ProcessInput` calls `ComputeFreeLook` (0xc71638), `UpdateFreeLookState` (0xc6c794) and `ComputeMovement`. Look and turn do not read `CFinalInput` directly; they go through `NSharedPlayerControls::GetAnalogInput(CStateManager const&, CSharedAimingCursor const&, NControlCommands::ECommand, CFinalInput const&, bool)` (0xc3a010) and `CCommandFrame::GetAnalogInput/GetDigitalHeldInput` (a command table at CStateManager+0x4E01C0 and +0x4E0320). Commands seen: 4/5 turn left/right, 60/61 look up/down, 67 free-look button, 94/95/96 gyro look parameters, 101 gyro-state button. Three control schemes branch on `NSharedPlayerControls::GetGameCubeFreelookControl`, `GetGyroFreelookControl` and `GetGunFollowsPointer`. `UpdateFreeLookState_Gyro` (0xc6cb30) turned out to be only the free-look on/off state for the gyro scheme (it reads a held command and seeds `FreeLookPitchAngle` from the camera transform), not the angular input. The gyro and pointer motion itself is produced by `CNXSixAxisAnalysis::UpdateMotion/UpdateCursor`. [B]

| Rank | Hook point | Address | Plan | Evidence |
|---|---|---|---|---|
| 1 | `CPlayerMP1::ProcessInput(CFinalInput const&, CStateManager&)` | 0xc70334 (4212 B) | Trampoline. Before the original: add the frame's mouse delta to the player yaw (`CActorMP1::SetTransform` 0xc4d588) and to `FreeLookPitchAngle` (CPlayerMP1+0x5cc), clamped to `CTweakPlayerMP1+0x138`. Gives direct angles, no stick shaping. Called 3 times from `GameMainLoop`; skip while orbit-locked, morphed or scanning (state fields: `GetMoveState` +0x3f0, `GetMorphBall` +0x9d0). | [B]. [M] practice mod and Rando both trampoline it by mangled name. Field offsets 0x5cc (9 `CPlayerMP1::` functions use it), 0x3f0 (28), 0x9d0 (46) and tweak +0x138 (2) are confirmed by instructions. |
| 2 | `NSharedPlayerControls::GetAnalogInput(...)` | 0xc3a010 (452 B) | The funnel for every analog command. Substituting commands 4/5/60/61 here makes the game's own free-look smoothing (`UpdateLookUp` 0xc3ab00, `GetTurnInput` 0xc3af60) apply, and the same funnel carries the button commands for item 2 of the next section. Yields a turn rate, not an angle, so it is the fallback for aim and the primary for buttons. | [B] decompiled |
| 3 | `CPlayerMP1::ComputeFreeLook(CFinalInput const&, CStateManager const&)` | 0xc71638 | Post-hook to overwrite the desired pitch/up vector after the engine's own computation. | [B] |
| 4 | `CFirstPersonCameraMP1::Think(float, CStateManager&)` / `UpdateTransform(CStateManager&, float)` | 0xd72314 / 0xd710ac (4392 B) | Late-sample hook: add the newest mouse delta to the camera after the tick, so look latency drops to one frame instead of one tick; fold the same value into the next tick so aim and view agree. | [B]. [M] practice mod hooks `Think` (roll). [P] "preview of the next tick" design. |
| 5 | `CNXSixAxisAnalysis::UpdateMotion` 0x359dac / `UpdateCursor` 0x35a098, `CNXJoyCon_NPad::ProcessAxis` | | Emulate the gyro/pointer device: the mouse becomes a virtual Joy-Con pointer, so the game's native "gun follows pointer" scheme (`GetGunFollowsPointer`, `CReticlePointerCenter`, `CSharedAimingCursor`) does the rest. Only needs the `nn::hid::GetSixAxisSensorState` import, which main already has. Worth a spike because it keeps the retail reticle and aim assist (`UpdateAssistedAiming` 0xc68e74). | [B] symbols and call structure |
| 6 | `CFinalInput::GetAnalog(EControl)` | 0x3520c0 (1760 B) | Inject RIGHT_STICK_X/Y (EControl 0x18, 0x15). Simplest, fully scheme-independent, but turn rate only. | [B]. [M] EControl table in `CFinalInput.hpp`. |

Lock-on: `CPlayerMP1::BreakOrbit(EOrbitBrokenType, CStateManager&)` 0xc775c8 is how the practice mod drops the lock [M, B]. Orbit state lives in `UpdateOrbit*` (0xc76d90..0xc77a94). Morph ball camera is `CBallCameraMP1::Think` 0xcff7ec. Gyro sensitivities are saved options (`CGameOptionsMP1::GetCameraGyroSensitivity/GetCursorGyroSensitivity(EControlScheme)` 0xc85cc4 / 0xc85cfc). Sensitivity units, pitch limit (87 degrees in the port; retail value comes from the tweak) and per-state behaviour are in the working notes `work/kb/notes/port_design.md` section 2.

## 2. Keyboard and mouse button synthesis

| Rank | Hook point | Address | Plan | Evidence |
|---|---|---|---|---|
| 1 | Import `nn::hid::GetNpadState(NpadFullKeyState*, uint const&)` and the JoyDual and Handheld overloads | import | Implement natively: fill buttons and both sticks from SDL pads, keyboard and mouse. No game code touched, works for menus and gameplay alike. Also `GetSixAxisSensorState`, `IsSixAxisSensorAtRest`, `GetTouchScreenStates<16>`, `SendVibrationValue` are imported (rumble, gyro, touch). | [B] full import list. |
| 2 | `CNXJoyCon_NPad::ProcessButtons` 0x35847c (1080 B), `ProcessStickAxis` 0x3581ac | 0x35847c | Second layer: converts `SGenericNpadState` into `CControllerGamepadData`. Use it if raw NpadState synthesis hits quirks (style detection, handheld vs docked). | [B] |
| 2b | Action layer: `NSharedPlayerControls::GetAnalogInput` 0xc3a010, `CCommandFrame::GetDigitalHeldInput/PressedInput/GetAnalogInput`, `NControlCommands::GetDataEnumValueForCommand` | 0xc3a010 | The scheme-to-command map is data-driven (remappable), so synthesizing at the Npad layer does not depend on it; synthesizing commands here avoids having to know the scheme. | [B] decompiled |
| 3 | `CFinalInput::GetDigitalHeld/Pressed/Released(EControl)` | 0x353160 / 0x3531a4 / 0x3531e8 (68 B each) | Final layer; the practice mod reads hotkeys here. EControl has 0x38 entries (A=0x1f ... ZR=0x26, PLUS=0x28, stick clicks 0x2b/0x2c). | [B], [M] `CFinalInput.hpp` |
| 4 | `COsContext::GetOsMouseState/GetOsKeyState/SetKeyDown/SetKeyUp/SetCaptureMouse/EnumerateChangedKeys` | 0xdbc / 0xde4 / 0xddc / 0xde0 / 0xdd8 / 0xdec | The engine's PC input API exists as stubs on Switch (`GetOsMouseState` returns a zeroed struct, `SetCaptureMouse` is a bare `ret`). Zero direct callers, so they are reached through a vtable or not at all. Worth a look in IDA before building a parallel path. | [B] disassembly |
| 5 | `CNXTouchScreen::ProcessTouchScreenData` 0x35a5b8, `CFinalInput::GetCursorPosition` 0x3532c4 | | Menu pointer: synthesize touch from the mouse for menus, map and inventory. | [B] symbols only |

Starting layout: [P] `work/kb/notes/port_design.md` section 1 (WASD, LMB fire, RMB lock-on, MMB missile, Space, Ctrl morph, Tab map, 1-4 beams, 5-8 visors, contexts and tap/hold/double-tap/toggle).

## 3. High refresh rate and timestep

What the retail loop does (decompiled `CGameArchitectureSupport::Update(float*)`, 0x3c81c8, in IDA on the validated `main.elf`): each call to `Update` (once per rendered frame, called from `CGameArchitecture::Update` 0x3c6f3c) measures real elapsed time with `nn::os::GetSystemTick`, clamps it to at most one tick, adds it to an accumulator, then runs a `do { ... } while (accum >= 1/60)` loop. The body always runs at least once. Each iteration queues `BeginSimulationTick(0.016667)`, `CInputGenerator::Update(..., 1/60)`, `TimerTick`, `UpdateAreaLoadState`, `EndSimulationTick`, then subtracts 1/60 from the accumulator. After the loop it queues `UpdateRenderState(simulated seconds)` and spends leftover frame time (budget 0.014 s) on `ExtraProcessingTick` and graveyard processing. Consequences: the logic step is a literal `0.016667f` per call, so the game only runs at the right speed when `Update` is called at 60 Hz; there is no frame-rate independence in this function and the 14 ms budget is also hard-coded. [B]

| Rank | Hook point | Address | Plan | Evidence |
|---|---|---|---|---|
| 1 | `CGameArchitectureSupport::Update(float*)` | 0x3c81c8 (1444 B) | Replace the `0.016667f` immediates (tick duration, accumulator compare, input `dt`) with the measured frame time clamped to a ceiling, or run a fixed small step several times per frame. Only this function needs changing. The community "Unlocked FPS" patch edits exactly this function (+0x140 = 0x3c8308). | [B] decompiled, [W] Fl4sh_ 120/240/Unlocked FPS |
| 2 | `CStateManagerGameLogicMP1::GameMainLoop(CStateManager&, CStateManagerUpdateAccess&, float dt)` | 0xc5bc4c (2436 B) | The consumer of that `dt`; scale or clamp here if the message path is awkward. Also calls `CPlayerMP1::ProcessInput` three times. | [B], [M] practice mod |
| 3 | `CPlayerMP1::GetDampedClampedVelocityWR(CStateManager const&, float) const` | 0xcee29c (patch sites +0x80, +0x14c, +0x17c = 0xcee31c, 0xcee3e8, 0xcee418) | Per-tick friction. The GameCube port's audit found this function family wrong above 60 Hz (a fixed friction subtracted every tick slows walking). The 120 FPS community patch rewrites the `fmov s1,#3.5` at +0x14c; the practice mod notes that merely hooking 0xcee418 turned physics to ice. First place to test at 120/240. | [B] names and sites; [W]; [M]; [P] `HIGH_FPS_AUDIT.md` |
| 4 | `CDynamicResolutionControl::Update(CRenderTimer const&, float)` / `GetResolutionScale` | 0x3c042c (756 B) / 0x3c08a0 | The 120 FPS patch rewrites both (it retargets the controller's frame-time goal). With a fixed resolution scale these can be stubs. | [B], [W] |
| 5 | `CGraphicsContext_NVN::PresentWindow(NVNqueue&)`, `NRenderUtilMPT::TickRenderTimings()` | 0x1a6a5c, 0xc32890 | Swap interval read at +0x38 (0x1a6a94) and render timing sampling; both touched by the 120 FPS patch. Ours is a Vulkan present, so these become host-side policy. | [B], [W] |
| 6 | `CStopwatch::GetElapsedTime`, `nn::os::GetSystemTick`, `CMain::RsMain`, `CGameArchitecture::Run` | 0x119dfc, import, 0x400, 0x3c66cc | Wall-clock source (host clock replaces the tick import). | [B] |

The GC port's counter list in `HIGH_FPS_AUDIT.md` (friction, cloak delay, wall sparks, decal frame index, particle seeds, `CBallCamera` short-move counter, HUD memo counter) is the checklist for the physics probe; MPR class names carry an `MP1` suffix. theboy181 claimed correct physics at 120 FPS in Ryujinx (news report only, patch unreleased); Fl4sh_'s patches are the only public implementation.

## 4. Field of view

| Rank | Hook point | Address | Plan | Evidence |
|---|---|---|---|---|
| 1 | `CGameCameraMP1::UpdateFOV(float)` | 0xcb9af0 (148 B) | Trampoline; write `CGameCameraMP1+0x25c` (current vertical FOV) after the original. One caller: `CCameraManagerMP1::UpdateCameras` 0xc8ce10. | [B], [M] practice mod |
| 2 | `CCameraManagerMP1::GetDefaultFirstPersonVerticalFOV()` / `...ThirdPerson...` | 0xc8c8b8 / 0xc8c8ac | Tiny getters; retail third-person is `mov w8,#0x42700000` (60.0) and first-person loads a data float (`adrp 0x20e7000; ldr s0,[x8,#0xa70]`, so the value sits in rodata). The community mods overwrite both with 80.0 and 74.0 immediates. Patching the getters changes spawn FOV only; `UpdateFOV` still drives it per frame. Three callers for first person (`CFirstPersonCameraMP1GOC::Create`, `CBallCameraMP1::SetState`, `CAnimatedCameraMP1::DoAnimatingState`). | [B], [W] |
| 3 | `CCameraManagerMP1::ConvertMP1HorizontalFovToRS14VerticalFov(float, EMP1FovType)` | 0xc9052c | The MP1 designs are specified horizontally; this converts to the engine's vertical FOV. Hook here for a correct ultrawide Hor+ conversion. | [B] symbol |

## 5. Resolution, dynamic resolution, ultrawide

| Rank | Hook point | Address | Plan | Evidence |
|---|---|---|---|---|
| 1 | `COsContext::GetScreenWidth/Height`, `GetHandheldFull*`, `GetHandheldContent*` | 0x1248, 0x1250, 0x1258..0x1270 (8 B each) | Constant getters returning 1600x900 docked and 1024x576 handheld in the original. Replace the six functions; 16 and 17 call sites also use them directly (`IGraphicsContext::BuildContext` 0x1a5ca8, `CGameArchitecture` ctor/Update, `CGuiTextPane::Initialize`, `CInGameGuiManagerMP1`, `CInventoryScreenMP1`, `CVisorEffectManagerMP1`, `CHudBallInterfaceMP1`). The community mods patch the getters and each `bl` site; with function overrides the sites follow automatically. | [B] all 12 call-site claims in the Fl4sh patch confirmed as `bl` into these getters inside the named functions; [W] |
| 2 | Aspect ratio: `CDisplayManager::GetAspectRatio()` +4 (0xafe3d8, redirected to a cave that returns the new ratio), aspect constants at 0xafeb2c and `CGameRenderJob::RenderGamePass`+0x268 (0xb30490) | 0xafe3d4 | Ultrawide mod patches these to w/h (2.3889 for 3440x1440). `RenderGamePass`+0x21c (0xb30444) is a `bl CDynamicResolutionControl::GetResolutionScale` that the 120 FPS mod replaces with a constant 1.0. | [B], [W] |
| 3 | `CGuiCamera::GetProjectionState()` | 0xbd52fc (+0x6c reads `[x0,#0x110]`) | HUD aspect: the mod multiplies it by 1.34375 for 21:9 so the 16:9 HUD keeps its proportions. | [B], [W] |
| 4 | `CGraphicsContext_NVN::Resize(CGraphicsDevice_NVN&, CVector2i const&)` | 0x1a5fe8 | Swapchain/render-target size; ours is created by the NVN-to-Vulkan layer. | [B] symbol |
| 5 | Dynamic resolution off: `CPerformanceHintManager::RebuildSceneNode(CStateManager&)` at head; or `CDynamicResolutionControl::IsEnabled` 0x3c0720 / `SetDesc` 0x3c0364 | 0xaff5d4 | Kenji's "Disable Dynamic Resolution" writes `ret` (C0035FD6) at 0xaff5d4. [B] confirms that address is the head of `CPerformanceHintManager::RebuildSceneNode`. | [B], [W] |
| 6 | LOD bias: `CRenderModel::PickLodLevel` 0x1fbb58 (+4 = 0x1fbb5c: `cbz x9` to `b`), `PickLodLevels` (+4 = 0x1fbe40), `GetBiasedLodLevel` (+0x1c = 0x1fc6d4) | | Draw distance / LOD force. | [B], [W] |

Render targets that scale with the dynamic resolution context: `CDynamicResolutionContextSceneNodeProxy::Build` 0x3653bc, `NDynamicResolution::SDesc` 0x3652d0.

## 6. HUD

| Rank | Hook point | Address | Evidence |
|---|---|---|---|
| 1 | `CGuiFrame::Draw(CGuiRenderCommandState&, float, float, CGuiWidgetDrawParms const&) const` | 0xbd3b4c | Every GUIF frame draws through here. Pillarbox or scale the viewport here. [B] |
| 2 | `CSamusHudMP1::Draw` / `DrawHelmet` / `DrawTargetingReticle` | 0xcb01d8 / 0xcb00a0 / 0xcb049c | Practice mod toggles HUD, helmet and reticle through these. [B], [M] |
| 3 | `CAutoMapperMP1::Update(float, CStateManager const&, CGuiCamera const&, float, bool)` | 0xe5945c | Minimap / map screen. [B], [M] |
| 4 | `CGuiCamera::GetProjectionState`, `NRenderUtilMPT::BuildOrthoViewport(bool,float,float,CAABox2f&)`, `GetViewport` | 0xbd52fc, 0xc32790, 0xc328f0 | Ortho setup for 2D. [B] |
| 5 | `CInGameGuiManagerMP1::Draw`, `CInventoryScreenMP1::Draw`, `CGuiTextPane::Initialize` | via the 12 call sites above | They call `GetScreenWidth/Height` directly. [B] |

Menus: the pause and front-end screens may be Scaleform (`GFXL`); no GFXL assets exist in the pak census; the menus are GUIF frames unless the unidentified SVGM type (89 assets) carries them (see `assets.md`).

## 7. Tonemap and HDR

| Rank | Hook point | Address | Plan | Evidence |
|---|---|---|---|---|
| 1 | `CRenderPass_Tonemap::Render(CGraphicsDeviceContext&, CGraphicsFrameBufferToken&, ...)` | 0x3a5a7c (1428 B) | The final-image pass. Replace its output transform with an HDR10/scRGB path. | [B] symbol |
| 2 | `NTonemap::build_tonemap_eval_params(STonemapParams const&)` | 0x211c60 (448 B) | Trampoline; practice mod subtracts a value from `STonemapParams+0x0` (inverse exposure) before calling the original. 7 direct callers (`CSceneTonemapParams` ctor 0x20f048, `CRenderPass_Tonemap` ctor 0x3a57e8 and `BindMaterialData` 0x3a6010 ...). Companions: `BuildFilmic` 0x211ac8, `BuildLinear` 0x211ab0, `set_inverse_exposure_system_value` 0x211e60. | [B], [M] |
| 3 | `CRenderPass_Tonemap::BuildBlendedColorLut(CGraphicsDeviceContext&, CColorGradeData const&)` | 0x3a60e0 (2000 B) | Per-room colour grade LUT. Keep it; apply HDR after the LUT. | [B] symbol |

## 8. Dev tools (warp, noclip, IGT, save position)

| Feature | Hook / call | Address | Evidence |
|---|---|---|---|
| Warp | `CGameStateMP1::SetCurrentWorldId(CObjectId)`, then `CGameStateMP1::CurrentWorldState()->SetDesiredAreaAssetId`, `CGameState::ContinueWithNewInitialState(CGameState&, SInitialState const&)`, then `CStateManager::GameInstanceState().QuitGame(kQR_Warp)` | 0xc838e4, 0x40a820 | [B] [M] practice mod `WarpMenu.cpp` (exact sequence stored as the `WarpRoutine (practice mod)` entry). World and area GUIDs are in the practice mod's `RegionEntries.h` (not copied here). |
| State pointers | `CGameStateManager::AssignNewGameState` and `CStateManager::InitializeState` capture `CGameState`/`CStateManager` | 0x412e78, 0xb01ce0 | [B] [M] Rando |
| IGT | `CGameState::GetPlayTime` is read at CGameState+0xffb08 (double); `SetTotalPlayTime(double)` | 0x40a178 | [M] practice mod; [B] setter. Offset not yet corroborated. |
| Save position | Read `CActorMP1::GetTransform` (CTransform4f) and `GetVelocityWR` / `SetVelocityWR` (`CPhysicsActorMP1`) in a `ProcessInput` trampoline | 0xc57874 | [B] [M] |
| Noclip / free camera | `CPlayerMP1::UpdateDebugCamera(CStateManager&)` is a 4-byte stub in the shipping build | 0xc69480 | [B] disassembly: `ret`. The practice mod instead overwrites transform every tick. |
| Stop time | `CStateManagerGameLogicMP1::SetGameState(EGameState)` (Running/SoftPaused/Paused) | 0xc60f48 | [B] [M] |
| Items / ammo / health | `CPlayerStateMP1::HasPowerUp`, `GetItemAmount`, `DecrPickUp`, `ItemEnabled`, `IncrPickUp`; power-up array at CPlayerStateMP1+0x44, 8 bytes per item {amount, capacity}. The cheat database uses a base 0x14 lower for the same array. | 0xc88ee8.. | [B] names (cheat sites 0xc89130 DecrPickUp+0x2c, 0xc88efc HasPowerUp+0x14, 0xc89180 GetItemAmount+0x40, 0xc89450 ItemEnabled+0x28); [M] |
| Invulnerable | `CStateManagerGameLogicMP1::ApplyLocalDamage` (+0x1f4 used by cheats), or write CHealthInfo via `CPlayerMP1::HealthInfo` | | [B] [M] |
| Escape-sequence timer | `CStateManagerGameLogicMP1::UpdateEscapeSequenceTimer` +0x30 is the "freeze time" cheat site | 0xc5dbb8 | [B] |
| Save/load | `CSaveGameManager::TrySave` 0x464bd4, `StartSaveOperation` 0x464770, `WriteSelfToOutputFileBuffer` 0x464924, `ReadSelfFromInputFileBuffer` 0x463d2c; file I/O imports `nn::fs::MountSaveData`, `MountRom` | | [B] |

## 9. Observed but not yet used

- `nvnBootstrapLoader` is the only NVN entry (import). Mods hook `nvnDeviceGetProcAddress` through it to intercept `nvnQueuePresentTexture`, `nvnWindowSetCrop` etc. The recompiler answers it directly. [B] [M]
- Audio goes through `nn::audio` (AudioRenderer API: voices, submixes, reverb, delay, aux, I3dl2). Movies go through `movie::` in `subsdk0` (Nintendo multimedia). No `nn::hid` keyboard or mouse API is imported at all. [B]
- Unresolved conflicts between sources (CStateManager+0x4e0150, SInitialState layout, CHealthInfoMP1 layout): `conflicts.json`.
