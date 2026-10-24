// SPDX-License-Identifier: GPL-3.0-or-later
// mpr.exe: Metroid Prime Remastered (Switch, 010012101468C000, v1.0.0) as a native Windows process.
//
// This is the part of the process that Horizon's kernel and loader do before the first guest instruction:
//   1. map the four NSOs of the ExeFS (rtld, main, sdk, subsdk0) at the bases the lifter baked into the generated code,
//   2. hand the lifted module tables to the runtime (each library carries the ABI version it was built with),
//   3. relocate / link the modules,
//   4. turn the host main thread into the guest main thread (stack, TLS in TPIDRRO_EL0, main thread handle),
//   5. enter the first module (rtld) at offset 0 with the registers the kernel gives a new process: x0 = 0, x1 = main thread handle.
// Everything after that (nn::init::Start, nninitStartup, nnMain) is the lifted game running on the runtime.
//
//   mpr [--game DIR] [--exefs DIR] [--ini FILE] [--log FILE] [--max-seconds N] [--link host|none] [--no-nvn] [--headless|--window]
// Environment: MPR_EXEFS, MPR_GAME. Keys (section [boot]) are read through the runtime's config, see docs/S6.md.
//
// Installed layout (a release folder after mpr_setup has run): when exefs\main sits next to mpr.exe, or --game DIR / MPR_GAME names a
// folder, that folder becomes the working directory, so everything the runtime reads relative to it (bc7_cache, shader_cache, romfs,
// controls.ini, mpr.log) is found wherever the exe is started from (double click, shortcut, terminal), the ExeFS is ./exefs and the
// settings file is ./mpr.ini (written by setup). Without it (development runs from game-build or work/run) nothing changes.
#include <windows.h>

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwctype>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "nxrt/config.h"
#include "nxrt/diag.h"
#include "nxrt/dispatch.h"
#include "nxrt/kernel.h"
#include "nxrt/log.h"
#include "nxrt/memory.h"
#include "nxrt/module.h"
#include "nxrt/gfx.h"
#include "nxrt/input_source.h"
#include "nxrt/nvn.h"
#include "nxrt/nvn_backend.h"
#include "nxrt/platform.h"
#include "nxrt/play.h"
#include "nxrt/nxmodule.h"
#include "nxrt/runtime.h"

extern "C" {
extern const NxModule nxmod_main, nxmod_sdk, nxmod_subsdk0, nxmod_rtld;
extern const uint32_t nxmod_main_abi, nxmod_sdk_abi, nxmod_subsdk0_abi, nxmod_rtld_abi;
}

#ifndef MPR_EXEFS_DEFAULT
#define MPR_EXEFS_DEFAULT "game/exefs"
#endif

#ifndef MPR_VERSION
#define MPR_VERSION "dev"     // set by the build: game-build/CMakeLists.txt, -DMPR_VERSION=0.1.0
#endif

namespace {

struct GameModule {
    const char* file;            // name of the NSO in the ExeFS
    const NxModule* nx;
    const uint32_t* abi;
    uint64_t base;               // must equal nx->base: the generated code has the address baked in
};

// Load order = the order the console maps them: the entry module first.
const GameModule kModules[] = {
    {"rtld", &nxmod_rtld, &nxmod_rtld_abi, 0x7700000000ull},
    {"main", &nxmod_main, &nxmod_main_abi, 0x7100000000ull},
    {"sdk", &nxmod_sdk, &nxmod_sdk_abi, 0x7500000000ull},
    {"subsdk0", &nxmod_subsdk0, &nxmod_subsdk0_abi, 0x7600000000ull},
};

// ---- the first 0xd8 bytes of rtld ------------------------------------------------------------------------------------------
// The lifter found no function at rtld offset 0 (the NSO entry: no symbol, no .eh_frame entry, nothing branches to it), so the
// straight-line code from offset 0 to 0xd4 is not in the lifted table although everything it calls is. This host function stands
// in for it, instruction for instruction (rtld disassembled from the dump, v1.0.0):
//   0x08  cmp x0, #0 ; b.ne 0xd8              x0 != 0: the kernel's entry for a user exception (not handled here)
//   0x10  w19 = w1                            main thread handle
//   0x14  memset(bss, 0, size)                bss at 0x32a0..0x33b0: already zero in the fresh mapping
//   0x48  x0 = module base ; x1 = &_DYNAMIC   (0x3010)
//   0x78  f_13c0(x0, x1)                      rtld's self-relocation (RELATIVE entries, addend based: idempotent after the host link)
//   0x84  f_04b0(x0, x1)                      the dynamic linker: finds the other modules with svcQueryMemory, relocates them
//   0x88  nn::init::Start(w19, GOT[0x3288], base+0x138c, base+0x820, base+0x870)   (through the PLT stub at 0x1700); never returns
// Registered only when the lifted table has no function at the entry (a lifter that learns the entry makes this unused).
constexpr uint64_t kRtldBase = 0x7700000000ull;
// Diagnostic probe, [boot] probe = no-sdk-services: nn::init::Start (sdk 0x2a8100) written out step by step, minus the one step that
// talks to Horizon services (nninitInitializeSdkModule: lm, appletOE, ...), so the rest of the start-up can be exercised before the
// service library exists. The order is the one in Start's disassembly:
//   _init_libc0 ; nnosInitialize(handle, exception handler) ; rtld+0x138c ; _init_libc1 ; [nninitInitializeSdkModule] ; nninitStartup ;
//   _init_libc2 ; rtld+0x820 (every module's constructors) ; nnMain ; rtld+0x870 ; nninitFinalizeSdkModule ; nnosQuickExit
void call_named(::Ctx* c, const char* name) {
    const uint64_t a = nxrt::nxmodule_find_export(name);
    if (!a) { NXLOG_E("boot", "probe: no module defines %s", name); nxrt::trap("probe: missing function", 0); }
    NXLOG_I("boot", "probe: %s at 0x%llx", name, static_cast<unsigned long long>(a));
    nxrt::dispatch_call(c, a);
}
void probe_start(::Ctx* c, uint32_t handle, uint64_t exception_handler) {
    const uint64_t b = kRtldBase;
    NXLOG_W("boot", "PROBE no-sdk-services: nn::init::Start is replaced by its steps without nninitInitializeSdkModule");
    call_named(c, "_init_libc0");
    c->x[0] = handle; c->x[1] = exception_handler;
    call_named(c, "nnosInitialize");
    nxrt::dispatch_call(c, b + 0x138c);
    call_named(c, "_init_libc1");
    call_named(c, "nninitStartup");
    call_named(c, "_init_libc2");
    nxrt::dispatch_call(c, b + 0x820);
    call_named(c, "nnMain");
    nxrt::dispatch_call(c, b + 0x870);
    call_named(c, "nninitFinalizeSdkModule");
    call_named(c, "nnosQuickExit");
}

void rtld_entry(::Ctx* c) {
    const uint64_t b = kRtldBase;
    if (c->x[0] != 0) {
        NXLOG_E("boot", "rtld entered for a user exception (x0 = 0x%llx): not implemented", static_cast<unsigned long long>(c->x[0]));
        nxrt::trap("rtld exception entry", c->x[0]);
    }
    const uint32_t handle = static_cast<uint32_t>(c->x[1]);
    c->x[0] = b;
    c->x[1] = b + 0x3010;
    nxrt::dispatch_call(c, b + 0x13c0);
    if (nxrt::config_get_str("boot", "link", "rtld") != "host") {
        c->x[0] = b;
        c->x[1] = b + 0x3010;
        nxrt::dispatch_call(c, b + 0x4b0);
    }
    if (nxrt::config_get_str("boot", "probe", "") == "no-sdk-services") {
        probe_start(c, handle, *reinterpret_cast<const uint64_t*>(b + 0x3288));
        return;
    }
    c->x[0] = handle;
    c->x[1] = *reinterpret_cast<const uint64_t*>(b + 0x3288);
    c->x[2] = b + 0x138c;
    c->x[3] = b + 0x820;
    c->x[4] = b + 0x870;
    nxrt::dispatch_call(c, b + 0x1700);
    NXLOG_E("boot", "nn::init::Start returned (x0 = 0x%llx): rtld would loop here", static_cast<unsigned long long>(c->x[0]));
    nxrt::trap("nn::init::Start returned", c->x[0]);
}

// rtld+0x138c is the third function pointer rtld hands to nn::init::Start (the SDK calls it at exit). It is five instructions with no
// symbol and no .eh_frame entry, reached only through a pc-relative data word, so the lifter has no function there either:
//   138c  mov x0, x30 ; bl 0x1398          0x1398: x2 = 0x1394 + [0x1394] = rtld+0x3008 ; [x2] = 1 ; x30 = x0 ; ret
// i.e. it stores 1 in the word at rtld+0x3008 and returns to its caller.
void rtld_fn_138c(::Ctx*) { *reinterpret_cast<uint32_t*>(kRtldBase + 0x3008) = 1; }

// Diagnostic ([boot] trace_plt = 1): wraps rtld's lazy PLT resolver (rtld+0x1318) and logs every binding: the slot, the link map, the
// relocation index and what the lifted lookup (rtld+0x8b0) answers, before the resolver runs for real (debug note 018).
nxrt::GuestFn g_orig_resolver = nullptr;
void traced_resolver(::Ctx* c) {
    const uint64_t slot = *reinterpret_cast<const uint64_t*>(c->x[31]);     // x16 pushed by PLT0
    const uint64_t got2 = c->x[16];
    const uint64_t idx = (slot - got2 - 8) / 8;
    const uint64_t lm = *reinterpret_cast<const uint64_t*>(got2 - 8);
    ::Ctx tmp = *c;
    tmp.x[0] = lm; tmp.x[1] = idx; tmp.x[17] = slot; tmp.x[30] = 0;
    nxrt::dispatch_call(&tmp, kRtldBase + 0x8b0);
    NXLOG_I("boot", "plt resolve: slot=0x%llx got2=0x%llx lm=0x%llx idx=%llu -> 0x%llx (GOT slot now 0x%llx)", (unsigned long long)slot,
            (unsigned long long)got2, (unsigned long long)lm, (unsigned long long)idx, (unsigned long long)tmp.x[0],
            (unsigned long long)*reinterpret_cast<const uint64_t*>(slot));
    g_orig_resolver(c);
}

std::unique_ptr<nxrt::gfx::Device> g_gfx_device;
std::unique_ptr<nxrt::gfx::Renderer> g_gfx_renderer;

// TEMP debug 121: dump the killer slots at a fault
LONG CALLBACK dump_killer(PEXCEPTION_POINTERS ep) {
    if (ep->ExceptionRecord->ExceptionCode != 0xC0000005) return EXCEPTION_CONTINUE_SEARCH;
    static int once = 0;
    if (once++) return EXCEPTION_CONTINUE_SEARCH;
    const uint8_t* base = reinterpret_cast<const uint8_t*>(0x710455d5b8ull);
    for (int slot = 0; slot < 2; slot++) {
        const uint8_t* k = base + 0x100 + slot * 0xd8;
        const uint64_t ids = *reinterpret_cast<const uint64_t*>(k + 0x58);
        const uint32_t n = *reinterpret_cast<const uint32_t*>(k + 0x50);
        NXLOG_E("dbg", "killer slot %d: tex ids ptr 0x%llx count %u (cap %u)", slot, (unsigned long long)ids, n, *reinterpret_cast<const uint32_t*>(k + 0x54));
        if (ids) { std::string t; for (uint32_t i = 0; i < n && i < 64; i++) { char b[16]; std::snprintf(b, 16, "%x ", reinterpret_cast<const uint32_t*>(ids)[i]); t += b; } NXLOG_E("dbg", "  ids: %s", t.c_str()); }
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

DWORD WINAPI killer_poll(LPVOID) {
    const uint8_t* base = reinterpret_cast<const uint8_t*>(0x710455d5b8ull);
    uint32_t last[2] = {0, 0};
    for (;;) {
        for (int slot = 0; slot < 2; slot++) {
            const uint32_t n = *reinterpret_cast<const volatile uint32_t*>(base + 0x100 + slot * 0xd8 + 0x50);
            if (n != last[slot]) {
                if (n > last[slot] && last[slot] == 0) {
                    std::string t;
                    for (const auto& r : nxrt::diag_threads()) {
                        if (!r.ctx) continue;
                        char b[96]; std::snprintf(b, sizeof b, "\n  %s fn=%llx lr=%llx:", r.name.c_str(), (unsigned long long)r.ctx->fn, (unsigned long long)r.ctx->x[30]); t += b;
                        uint64_t f = r.ctx->x[29];
                        for (int d = 0; d < 10 && f > 0x1000 && !(f & 7); d++) { std::snprintf(b, sizeof b, " %llx", (unsigned long long)*reinterpret_cast<const uint64_t*>(f + 8)); t += b; f = *reinterpret_cast<const uint64_t*>(f); }
                    }
                    NXLOG_E("dbg", "killer slot %d count %u -> %u%s", slot, last[slot], n, t.c_str());
                }
                last[slot] = n;
            }
        }
    }
    return 0;
}

[[noreturn]] void die(const char* fmt, const char* a = "", const char* b = "") {
    NXLOG_E("boot", fmt, a, b);
    nxrt::log_flush();
    std::fprintf(stderr, "mpr: ");
    std::fprintf(stderr, fmt, a, b);
    std::fprintf(stderr, "\n");
#ifdef MPR_GUI_SUBSYSTEM
    char msg[1024];     // a double-clicked exe has no console: say what is wrong in a box
    std::snprintf(msg, sizeof msg, fmt, a, b);
    MessageBoxA(nullptr, msg, "Metroid Prime Remastered", MB_OK | MB_ICONERROR);
#endif
    TerminateProcess(GetCurrentProcess(), 1);
    for (;;) {}
}

std::wstring widen_utf8(const std::string& s) {
    if (s.empty()) return {};
    const int n = MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), nullptr, 0);
    std::wstring w(static_cast<size_t>(n), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), w.data(), n);
    return w;
}
std::string narrow_utf8(const std::wstring& w) {
    if (w.empty()) return {};
    const int n = WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), nullptr, 0, nullptr, nullptr);
    std::string s(static_cast<size_t>(n), '\0');
    WideCharToMultiByte(CP_UTF8, 0, w.data(), static_cast<int>(w.size()), s.data(), n, nullptr, nullptr);
    return s;
}
std::wstring exe_dir() {
    std::wstring buf(32768, L'\0');
    const DWORD n = GetModuleFileNameW(nullptr, buf.data(), static_cast<DWORD>(buf.size()));
    buf.resize(n);
    const size_t slash = buf.find_last_of(L"\\/");
    return slash == std::wstring::npos ? L"." : buf.substr(0, slash);
}
bool file_exists(const std::wstring& p) {
    const DWORD a = GetFileAttributesW(p.c_str());
    return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}
// Absolute form of a path given on the command line, resolved against the current directory (before it is changed).
std::string absolute_utf8(const std::string& p) {
    const std::wstring w = widen_utf8(p);
    std::wstring buf(32768, L'\0');
    const DWORD n = GetFullPathNameW(w.c_str(), static_cast<DWORD>(buf.size()), buf.data(), nullptr);
    if (!n || n >= buf.size()) return p;
    buf.resize(n);
    return narrow_utf8(buf);
}

// [boot] press = "A@12,A@20:500,PLUS@30,A#1500": scripted controller presses on player 1 (button@seconds-after-start[:hold ms, default 300]).
// "A#1500:300" is keyed to the NVN back end's presented-frame count instead of seconds: a loaded machine plays the same sequence.
struct ScriptedPress { uint64_t bit; double at; int hold_ms; bool by_frame = false; };
std::shared_ptr<nxrt::hid::ManualInputSource> g_pad;
std::vector<ScriptedPress> g_presses;
DWORD WINAPI press_thread(LPVOID) {
    const ULONGLONG t0 = GetTickCount64();
    for (const ScriptedPress& p : g_presses) {
        if (p.by_frame) {
            while (!nxrt::nvn::backend_installed() || nxrt::nvn::backend_stats().presents < static_cast<uint64_t>(p.at)) Sleep(20);
            NXLOG_I("boot", "scripted press at present %.0f (%.1f s)", p.at, (GetTickCount64() - t0) / 1000.0);
        } else {
            const ULONGLONG due = t0 + static_cast<ULONGLONG>(p.at * 1000);
            for (ULONGLONG now = GetTickCount64(); now < due; now = GetTickCount64()) Sleep(static_cast<DWORD>(due - now > 50 ? 50 : due - now));
            NXLOG_I("boot", "scripted press at %.1f s", p.at);
        }
        g_pad->press(0, p.bit);
        Sleep(p.hold_ms);
        g_pad->release(0, p.bit);
    }
    return 0;
}
void parse_presses(const std::string& spec) {
    using namespace nxrt::hid;
    static const struct { const char* n; NpadButtonBit b; } names[] = {{"A", kBtnA}, {"B", kBtnB}, {"X", kBtnX}, {"Y", kBtnY}, {"PLUS", kBtnPlus},
        {"MINUS", kBtnMinus}, {"UP", kBtnUp}, {"DOWN", kBtnDown}, {"LEFT", kBtnLeft}, {"RIGHT", kBtnRight}, {"L", kBtnL}, {"R", kBtnR}, {"ZL", kBtnZL}, {"ZR", kBtnZR}};
    size_t i = 0;
    while (i < spec.size()) {
        size_t j = spec.find(',', i);
        if (j == std::string::npos) j = spec.size();
        const std::string item = spec.substr(i, j - i);
        i = j + 1;
        size_t at = item.find('@');
        const bool by_frame = at == std::string::npos && item.find('#') != std::string::npos;
        if (by_frame) at = item.find('#');
        if (at == std::string::npos) continue;
        const std::string name = item.substr(0, at);
        const size_t colon = item.find(':', at);
        ScriptedPress sp{0, std::atof(item.c_str() + at + 1), colon == std::string::npos ? 300 : std::atoi(item.c_str() + colon + 1), by_frame};
        for (const auto& e : names) if (name == e.n) sp.bit = btn(e.b);
        if (sp.bit) g_presses.push_back(sp);
    }
}

// [boot] screenshot_at = N (seconds after start, repeatable through screenshot_every): the renderer writes work/run/shot_<n>.png of the presented frame.
DWORD WINAPI shot_thread(LPVOID) {
    const int64_t first = nxrt::config_get_int("boot", "screenshot_at", 0), every = nxrt::config_get_int("boot", "screenshot_every", 0);
    int n = 0;
    Sleep(static_cast<DWORD>(first * 1000));
    for (;;) {
        if (g_gfx_renderer) {
            char path[64];
            std::snprintf(path, sizeof path, "shot_%d.png", n++);
            g_gfx_renderer->request_screenshot(path);
            NXLOG_I("boot", "screenshot requested: %s", path);
        }
        if (every <= 0) break;
        Sleep(static_cast<DWORD>(every * 1000));
    }
    return 0;
}

DWORD WINAPI deadline_thread(LPVOID p) {
    const DWORD ms = static_cast<DWORD>(reinterpret_cast<uintptr_t>(p));
    Sleep(ms);
    NXLOG_W("boot", "max_seconds reached: the guest is still running; ending the process");
    nxrt::log_flush();
    if (nxrt::nvn::backend_installed()) {
        const nxrt::nvn::BackendStats b = nxrt::nvn::backend_stats();
        NXLOG_I("boot", "nvn back end at the deadline: submits %llu lists %llu draws %llu (skipped %llu) presents %llu pipelines %llu textures %llu (failed %llu) unsupported %llu",
                (unsigned long long)b.submits, (unsigned long long)b.lists_replayed, (unsigned long long)b.draws, (unsigned long long)b.draws_skipped,
                (unsigned long long)b.presents, (unsigned long long)b.pipelines_created, (unsigned long long)b.textures_created,
                (unsigned long long)b.textures_failed, (unsigned long long)b.unsupported_ops);
        NXLOG_I("boot", "nvn unsupported operations: %s", nxrt::nvn::backend_unsupported_report().c_str());
    }
    NXLOG_I("boot", "state at the deadline:\n%s", nxrt::summary().c_str());
    nxrt::log_flush();
    TerminateProcess(GetCurrentProcess(), 124);
    return 0;
}

// --prepare-shaders: no game, no window. A headless Vulkan device and the NVN back end's pipeline code compile the shader parts of every program the
// setup tool listed (shader_cache/programs.bin), so the driver has them in its cache before the first start. Progress goes to stdout as
// "prepare: <done> <total>" lines (the launcher reads them), the end as "prepare: done ..." / "prepare: ready" (already up to date).
// Exit code: 0 done or ready, 1 could not run, 3 cancelled.
int prepare_shaders_main(bool if_needed, int threads, const std::string& programs) {
    std::string err;
    nxrt::gfx::DeviceDesc dd;
    dd.headless = 1;
    auto dev = nxrt::gfx::Device::create(dd, &err);
    if (!dev) { std::printf("prepare: error graphics device: %s\n", err.c_str()); return 1; }
    nxrt::nvn::BackendDesc bd;
    bd.device = dev.get();
    bd.register_entry_points = false;
    if (!nxrt::nvn::install_backend(bd)) { std::printf("prepare: error the graphics back end did not start\n"); return 1; }
    nxrt::nvn::ShaderPrepareOptions po;
    po.only_if_needed = if_needed;
    po.programs_file = programs;
    po.threads = threads;
    auto last = std::chrono::steady_clock::now();
    po.progress = [&](uint64_t done, uint64_t total) {
        const auto now = std::chrono::steady_clock::now();
        if (done < total && now - last < std::chrono::milliseconds(250)) return true;
        last = now;
        std::printf("prepare: %llu %llu\n", static_cast<unsigned long long>(done), static_cast<unsigned long long>(total));
        std::fflush(stdout);
        return true;
    };
    nxrt::nvn::ShaderPrepareResult pr;
    const bool ok = nxrt::nvn::prepare_shaders(po, &pr);
    int rc = 0;
    if (!ok) { std::printf("prepare: error %s\n", pr.error.c_str()); rc = 1; }
    else if (pr.already_ready) std::printf("prepare: ready\n");
    else std::printf("prepare: done programs=%llu prepared=%llu missing=%llu failed=%llu parts=%llu fast=%llu seconds=%.1f%s\n", static_cast<unsigned long long>(pr.programs),
                     static_cast<unsigned long long>(pr.prepared), static_cast<unsigned long long>(pr.missing_shaders), static_cast<unsigned long long>(pr.failed),
                     static_cast<unsigned long long>(pr.parts), static_cast<unsigned long long>(pr.fast_parts), pr.seconds, pr.cancelled ? " cancelled" : "");
    std::fflush(stdout);
    if (ok && pr.cancelled) rc = 3;
    nxrt::nvn::shutdown_backend();
    dev.reset();
    nxrt::shutdown();
    return rc;
}

}  // namespace

int main(int argc, char** argv) {
#ifdef MPR_GUI_SUBSYSTEM
    // Started from a terminal: show the output there. When the output is redirected to a file or a pipe (mpr --version > v.txt), leave it alone.
    const HANDLE out_handle = GetStdHandle(STD_OUTPUT_HANDLE);
    if ((!out_handle || out_handle == INVALID_HANDLE_VALUE) && AttachConsole(ATTACH_PARENT_PROCESS)) {
        std::freopen("CONOUT$", "w", stdout);
        std::freopen("CONOUT$", "w", stderr);
    }
#endif
    std::string exefs = std::getenv("MPR_EXEFS") ? std::getenv("MPR_EXEFS") : MPR_EXEFS_DEFAULT;
    bool exefs_given = std::getenv("MPR_EXEFS") != nullptr;
    std::string game = std::getenv("MPR_GAME") ? std::getenv("MPR_GAME") : "";
    const char* ini = nullptr;
    const char* logp = nullptr;
    bool prepare = false, prepare_if_needed = false;      // --prepare-shaders [--if-needed] [--threads N]: compile the game's shaders ahead and exit (no game start)
    int prepare_threads = 0;
    std::string prepare_programs;                         // --programs FILE: another program list (tests)
    std::vector<std::pair<std::string, std::string>> boot_opts;   // [boot] keys from the command line: nxrt::init() reloads the configuration, so they are applied after it
    for (int i = 1; i < argc; i++) {
        auto arg = [&](const char* n) { return !std::strcmp(argv[i], n) && i + 1 < argc; };
        if (arg("--game")) game = argv[++i];
        else if (arg("--exefs")) { exefs = argv[++i]; exefs_given = true; }
        else if (arg("--ini")) ini = argv[++i];
        else if (arg("--log")) logp = argv[++i];
        else if (arg("--max-seconds")) boot_opts.emplace_back("max_seconds", argv[++i]);
        else if (arg("--link")) boot_opts.emplace_back("link", argv[++i]);
        else if (!std::strcmp(argv[i], "--version")) { std::printf("mpr %s\n", MPR_VERSION); return 0; }
        else if (!std::strcmp(argv[i], "--prepare-shaders")) { prepare = true; _putenv("NXRT_DIAG_WATCHDOG_SECONDS=0"); }
        else if (!std::strcmp(argv[i], "--if-needed")) prepare_if_needed = true;
        else if (arg("--threads")) prepare_threads = std::atoi(argv[++i]);
        else if (arg("--programs")) prepare_programs = argv[++i];
        else if (!std::strcmp(argv[i], "--no-nvn")) boot_opts.emplace_back("nvn", "0");
        else if (!std::strcmp(argv[i], "--headless")) boot_opts.emplace_back("gfx", "headless");
        else if (!std::strcmp(argv[i], "--window")) boot_opts.emplace_back("gfx", "window");
        else { std::fprintf(stderr, "mpr: unknown argument %s\n", argv[i]); return 2; }
    }

    // Installed layout: work from the game folder (see the file comment).
    std::string ini_abs, log_abs;
    bool installed = false;
    {
        const std::wstring base = game.empty() ? exe_dir() : widen_utf8(absolute_utf8(game));
        installed = !game.empty() || file_exists(base + L"\\exefs\\main");
        if (installed) {
            if (exefs_given) exefs = absolute_utf8(exefs);
            if (ini) { ini_abs = absolute_utf8(ini); ini = ini_abs.c_str(); }
            if (logp) { log_abs = absolute_utf8(logp); logp = log_abs.c_str(); }
            if (!SetCurrentDirectoryW(base.c_str())) die("cannot use the game folder %s", narrow_utf8(base).c_str());
            // One game (or one shader preparation) per game folder: two would write the same log, pipeline cache and saves. The name comes from
            // the folder's full path; NXRT_ALLOW_MULTIPLE=1 lifts the check for test rigs.
            if (!std::getenv("NXRT_ALLOW_MULTIPLE")) {
                std::wstring full(32768, L'\0');
                full.resize(GetFullPathNameW(base.c_str(), static_cast<DWORD>(full.size()), full.data(), nullptr));
                unsigned long long h = 1469598103934665603ull;
                for (wchar_t ch : full) h = (h ^ static_cast<unsigned long long>(std::towlower(ch))) * 1099511628211ull;
                const std::wstring name = L"Local\\MPRRecomp_" + std::to_wstring(h);
                if (CreateMutexW(nullptr, FALSE, name.c_str()) && GetLastError() == ERROR_ALREADY_EXISTS)
                    die("The game is already running from this folder (or its shaders are being prepared). Close that one first.");
            }
            if (!exefs_given) exefs = "exefs";
            if (!logp) logp = "mpr.log";
            if (!ini && !std::getenv("NXRT_INI") && file_exists(L"mpr.ini")) ini = "mpr.ini";
        }
    }

    nxrt::InitOptions opt;
    opt.ini_path = ini;
    opt.log_path = logp;
    if (!nxrt::init(opt)) die("runtime start-up failed (address-space layout)");
    for (const auto& kv : boot_opts) nxrt::config_set("boot", kv.first.c_str(), kv.second.c_str());
    if (installed && !nxrt::config_has("fs", "romfs")) nxrt::config_set("fs", "romfs", "romfs");   // mpr.ini missing or without [fs]
    nxrt::config_set("process", "program_id", "0x010012101468C000");     // GetInfo(ProgramId); an ini value or the environment still wins
    NXLOG_I("boot", "mpr %s (Metroid Prime Remastered PC port)", MPR_VERSION);
    NXLOG_I("boot", "Metroid Prime Remastered v1.0.0: exefs '%s'", exefs.c_str());

    if (prepare) return prepare_shaders_main(prepare_if_needed, prepare_threads, prepare_programs);

    bool play_started = false;
    if (nxrt::config_get_bool("boot", "nvn", true)) {
        nxrt::nvn::install();   // nvnBootstrapLoader and the NVN entry points (logging stubs for what no back end implements)
        // The NVN back end (Vulkan). [boot] gfx = window (the default for a normal launch: play mode, see docs/S8.md) | headless (an offscreen
        // image ring: tests and scripted runs; also the default when [gfx] headless / NXRT_GFX_HEADLESS is set) | none (keep the logging stubs).
        const std::string gfxmode = nxrt::config_get_str("boot", "gfx", nxrt::config_get_bool("gfx", "headless", false) ? "headless" : "window");
        if (gfxmode != "none") {
            const bool headless = gfxmode != "window";
            nxrt::play::DisplayConfig disp;
            if (!headless) {
                disp = nxrt::play::display();       // controls.ini: window size, present mode, frame cap
                nxrt::platform::init();
                nxrt::platform::WindowDesc wd;
                wd.title = "Metroid Prime Remastered";
                wd.width = disp.width;
                wd.height = disp.height;
                if (!nxrt::platform::create_window(wd)) die("cannot create the game window. The game needs a graphics driver with Vulkan 1.3: update the driver for your graphics card and try again. The reason is in mpr.log.");
            }
            nxrt::gfx::DeviceDesc dd;
            dd.headless = headless ? 1 : 0;
            std::string err;
            g_gfx_device = nxrt::gfx::Device::create(dd, &err);
            if (!g_gfx_device) die("graphics device: %s", err.c_str());
            nxrt::gfx::RendererDesc rd;
            rd.headless_width = 1920;
            rd.headless_height = 1080;
            if (!headless) rd.present_mode = disp.present_mode;
            g_gfx_renderer = nxrt::gfx::Renderer::create(*g_gfx_device, rd, &err);
            if (!g_gfx_renderer) die("renderer: %s", err.c_str());
            nxrt::nvn::BackendDesc bd;
            bd.device = g_gfx_device.get();
            bd.renderer = g_gfx_renderer.get();
            if (!headless) {
                bd.limiter = nxrt::play::limiter();        // the frame limiter paces the presenting thread
                bd.keep_aspect = disp.keep_aspect;
            }
            if (!nxrt::nvn::install_backend(bd)) die("NVN back end failed to start (see the log)");
            NXLOG_I("boot", "NVN back end running on %s (%s)", g_gfx_device->gpu().name.c_str(), headless ? "headless" : "window");
            nxrt::play::StartOptions po;
            po.device = g_gfx_device.get();
            po.renderer = g_gfx_renderer.get();
            po.window = !headless;
            po.overlay = !headless;
            nxrt::play::start(po);
            play_started = true;
        }
    }
    if (!play_started) {
        nxrt::play::StartOptions po;           // no graphics: play mode still turns scripted keys into pad input
        po.overlay = false;
        nxrt::play::start(po);
    }

    // 1. map
    for (const GameModule& g : kModules) {
        nxrt::LoadOptions lo;
        lo.name = g.file;
        lo.base = g.base;
        std::string err;
        const std::string path = exefs + "\\" + g.file;
        if (!file_exists(widen_utf8(path)))
            die("The game files were not found (%s). Run mpr_setup.exe from this folder first, then start the game again.", path.c_str());
        nxrt::Module* m = nxrt::module_load_nso_file(path.c_str(), lo, &err);
        if (!m) die("cannot load %s: %s", path.c_str(), err.c_str());
        if (m->base() != g.nx->base) die("module %s is mapped at a base different from the one the library was lifted for", g.file);
        // 2. register the lifted functions and tables (an ABI-version mismatch of a stale library is refused here)
        const nxrt::RegResult r = nxrt::nxmodule_register(m, g.nx, *g.abi);
        if (!r.ok()) die("lifted module %s refused: %s", g.file, r.message.c_str());
    }

    // The game reaches NVN only through `nvnBootstrapLoader` (an import of main that the sdk defines: Nintendo's driver). The lifted PLT
    // stub of main calls host_import(), not the GOT that rtld fills, so the symbol is forced to the runtime's NVN front end here; the
    // sdk's own definition is also replaced in the call table for any indirect call that reaches it by address (debug note 120).
    if (nxrt::config_get_bool("boot", "nvn", true)) {
        nxrt::module_override_symbol("nvnBootstrapLoader");
        if (const uint64_t def = nxrt::nxmodule_find_export("nvnBootstrapLoader"))
            if (nxrt::HleFn fn = nxrt::hle_lookup("nvnBootstrapLoader")) nxrt::fn_register(def, fn);
    }

    if (nxrt::config_get_bool("boot", "dump_killer", false)) { AddVectoredExceptionHandler(1, dump_killer); CreateThread(nullptr, 0, killer_poll, nullptr, 0, nullptr); }
    // 3. link: relocations of every module, imports between modules by symbol name, page protections
    //    [boot] link = rtld (default): the host only maps and protects; the game's own rtld (lifted) relocates every module, as on the console
    //    [boot] link = host: the runtime's linker relocates, rtld's linker step is skipped (a cross-check of the two)
    const std::string link = nxrt::config_get_str("boot", "link", "rtld");
    if (link == "host") {
        if (!nxrt::module_link_all()) die("linking the modules failed (see the log)");
    } else {
        nxrt::module_protect_all();
    }

    if (const std::string spec = nxrt::config_get_str("boot", "press", ""); !spec.empty()) {
        parse_presses(spec);
        g_pad = std::make_shared<nxrt::hid::ManualInputSource>();
        g_pad->connect(0, nxrt::hid::NpadStyle::FullKey);
        nxrt::hid::set_input_source(g_pad);
        CreateThread(nullptr, 0, press_thread, nullptr, 0, nullptr);
    }
    if (nxrt::config_get_int("boot", "screenshot_at", 0) > 0) CreateThread(nullptr, 0, shot_thread, nullptr, 0, nullptr);
    if (const int64_t s = nxrt::config_get_int("boot", "max_seconds", 0); s > 0)
        CreateThread(nullptr, 0, deadline_thread, reinterpret_cast<void*>(static_cast<uintptr_t>(s * 1000)), 0, nullptr);

    // 4. the main thread: the npdm of main says 1 MiB of stack, priority 44, core 0
    const uint64_t stack = static_cast<uint64_t>(nxrt::config_get_int("boot", "main_stack_kb", 1024)) << 10;
    const uint32_t h = nxrt::kernel::main_thread_adopt(stack, "main");
    if (!h) die("cannot create the main thread");
    ::Ctx* ctx = nxrt::kernel::current_ctx();

    if (!nxrt::fn_lookup(kModules[0].base)) {
        nxrt::fn_register(kModules[0].base, rtld_entry);
        NXLOG_W("boot", "the lifted rtld has no function at its entry: using the host stand-in (see rtld_entry)");
    }
    if (!nxrt::fn_lookup(kRtldBase + 0x138c)) {
        nxrt::fn_register(kRtldBase + 0x138c, rtld_fn_138c);
        NXLOG_W("boot", "the lifted rtld has no function at 0x138c: using the host stand-in (see rtld_fn_138c)");
    }

    if (nxrt::config_get_bool("boot", "trace_plt", false)) {
        g_orig_resolver = nxrt::fn_lookup(kRtldBase + 0x1318);
        if (g_orig_resolver) nxrt::fn_register(kRtldBase + 0x1318, traced_resolver);
    }

    // 5. the first instruction: rtld offset 0. x0 = 0 (the exception entry would be non-zero), x1 = the main thread's handle.
    const uint64_t entry = kModules[0].base;
    ctx->x[0] = 0;
    ctx->x[1] = h;
    ctx->x[30] = 0;
    NXLOG_I("boot", "entering %s at 0x%llx (x1 = main thread handle 0x%x)", kModules[0].file, static_cast<unsigned long long>(entry), h);
    nxrt::dispatch_call(ctx, entry);

    NXLOG_I("boot", "the entry function returned (x0 = 0x%llx): ending the process", static_cast<unsigned long long>(ctx->x[0]));
    nxrt::play::stop();
    nxrt::kernel::main_thread_release();
    nxrt::shutdown();
    return static_cast<int>(ctx->x[0] & 0xff);
}
