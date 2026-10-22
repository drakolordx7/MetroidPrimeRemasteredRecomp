# Fragment schema (docs/mpr/frag/*.json)

One file per source cluster, merged by `tools/analysis/kb_merge.py` into `docs/mpr/symbols.json` and `structs.json`.
A fragment is `{"source_id": "<short id>", "items": [ ... ]}`. Every item needs a `src` with an exact `evidence` string
that appears in the source file within +-3 lines of `line` (`kb_check.py` verifies this mechanically).
Nothing is invented: unknown values are `null`.

## symbol item
```
{"type":"symbol",
 "name":"CPlayerMP1::ProcessInput",       # qualified C++ name as best known (demangled), or the plain name from the source
 "mangled":"_ZN10CPlayerMP112ProcessInputERK11CFinalInputR13CStateManager" | null,
 "kind":"function|global|vtable|data|patch_site",
 "address":"0xc59814" | null,             # lowercase hex exactly as the source gives it
 "addr_form":"main_offset|va|unknown",    # main_offset = relative to start of main .text (VA = 0x7100000000 + offset); va = absolute
 "claimed_version":"1.0.0|unspecified",
 "signature":"void ProcessInput(const CFinalInput&, CStateManager&)" | null,
 "role":"one line, only what the source says or plainly implies",
 "tags":["input","camera","timestep","render","save","hud","tonemap","resolution","fov","physics","warp","igt","os","nvn","asset","script","player_state","collision","audio"],
 "used_by":"how the source uses it: trampoline hook | inline hook | offset patch | called | read",
 "src":{"path":"refs/<repo>/<file>","line":123,"evidence":"exact substring"}}
```
## struct item
```
{"type":"struct","name":"CPlayerMP1","bases":["CPhysicsActorMP1"],"size":"0x..." | null,
 "fields":[{"offset":"0x5cc","type":"float","name":"mFreeLookPitchAngle","note":"...","confidence":"source-stated|inferred",
            "src":{"path":"...","line":1,"evidence":"..."}}],
 "src":{...}}
```
## enum item
```
{"type":"enum","name":"EControl","underlying":"int","values":[{"name":"ZR","value":"0x26"}],"src":{...}}
```
Paths in `src.path` are relative to the project root `D:\AI\Active\Metroid-Prime` with forward slashes, e.g. `refs/mp1r-practice-mod/src/program/patches.cpp`.
