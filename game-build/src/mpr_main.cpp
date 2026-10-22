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
//   mpr [--exefs DIR] [--ini FILE] [--log FILE] [--max-seconds N] [--link host|none] [--no-nvn]
// Environment: MPR_EXEFS. Keys (section [boot]) are read through the runtime's config, see docs/S6.md.
#include <windows.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

#include "nxrt/config.h"
#include "nxrt/diag.h"
#include "nxrt/dispatch.h"
#include "nxrt/kernel.h"
#include "nxrt/log.h"
#include "nxrt/memory.h"
#include "nxrt/module.h"
#include "nxrt/nvn.h"
#include "nxrt/nxmodule.h"
#include "nxrt/runtime.h"

extern "C" {
extern const NxModule nxmod_main, nxmod_sdk, nxmod_subsdk0, nxmod_rtld;
extern const uint32_t nxmod_main_abi, nxmod_sdk_abi, nxmod_subsdk0_abi, nxmod_rtld_abi;
}

#ifndef MPR_EXEFS_DEFAULT
#define MPR_EXEFS_DEFAULT "game/exefs"
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

[[noreturn]] void die(const char* fmt, const char* a = "", const char* b = "") {
    NXLOG_E("boot", fmt, a, b);
    nxrt::log_flush();
    std::fprintf(stderr, "mpr: ");
    std::fprintf(stderr, fmt, a, b);
    std::fprintf(stderr, "\n");
    TerminateProcess(GetCurrentProcess(), 1);
    for (;;) {}
}

DWORD WINAPI deadline_thread(LPVOID p) {
    const DWORD ms = static_cast<DWORD>(reinterpret_cast<uintptr_t>(p));
    Sleep(ms);
    NXLOG_W("boot", "max_seconds reached: the guest is still running; ending the process");
    NXLOG_I("boot", "state at the deadline:\n%s", nxrt::summary().c_str());
    nxrt::log_flush();
    TerminateProcess(GetCurrentProcess(), 124);
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    std::string exefs = std::getenv("MPR_EXEFS") ? std::getenv("MPR_EXEFS") : MPR_EXEFS_DEFAULT;
    const char* ini = nullptr;
    const char* logp = nullptr;
    for (int i = 1; i < argc; i++) {
        auto arg = [&](const char* n) { return !std::strcmp(argv[i], n) && i + 1 < argc; };
        if (arg("--exefs")) exefs = argv[++i];
        else if (arg("--ini")) ini = argv[++i];
        else if (arg("--log")) logp = argv[++i];
        else if (arg("--max-seconds")) nxrt::config_set("boot", "max_seconds", argv[++i]);
        else if (arg("--link")) nxrt::config_set("boot", "link", argv[++i]);
        else if (!std::strcmp(argv[i], "--no-nvn")) nxrt::config_set("boot", "nvn", "0");
        else { std::fprintf(stderr, "mpr: unknown argument %s\n", argv[i]); return 2; }
    }

    nxrt::InitOptions opt;
    opt.ini_path = ini;
    opt.log_path = logp;
    if (!nxrt::init(opt)) die("runtime start-up failed (address-space layout)");
    nxrt::config_set("process", "program_id", "0x010012101468C000");     // GetInfo(ProgramId); an ini value or the environment still wins
    NXLOG_I("boot", "Metroid Prime Remastered v1.0.0: exefs '%s'", exefs.c_str());

    if (nxrt::config_get_bool("boot", "nvn", true)) nxrt::nvn::install();   // nvnBootstrapLoader and the NVN entry points (logging stubs until implemented)

    // 1. map
    for (const GameModule& g : kModules) {
        nxrt::LoadOptions lo;
        lo.name = g.file;
        lo.base = g.base;
        std::string err;
        const std::string path = exefs + "\\" + g.file;
        nxrt::Module* m = nxrt::module_load_nso_file(path.c_str(), lo, &err);
        if (!m) die("cannot load %s: %s", path.c_str(), err.c_str());
        if (m->base() != g.nx->base) die("module %s is mapped at a base different from the one the library was lifted for", g.file);
        // 2. register the lifted functions and tables (an ABI-version mismatch of a stale library is refused here)
        const nxrt::RegResult r = nxrt::nxmodule_register(m, g.nx, *g.abi);
        if (!r.ok()) die("lifted module %s refused: %s", g.file, r.message.c_str());
    }

    // 3. link: relocations of every module, imports between modules by symbol name, page protections
    //    [boot] link = rtld (default): the host only maps and protects; the game's own rtld (lifted) relocates every module, as on the console
    //    [boot] link = host: the runtime's linker relocates, rtld's linker step is skipped (a cross-check of the two)
    const std::string link = nxrt::config_get_str("boot", "link", "rtld");
    if (link == "host") {
        if (!nxrt::module_link_all()) die("linking the modules failed (see the log)");
    } else {
        nxrt::module_protect_all();
    }

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

    // 5. the first instruction: rtld offset 0. x0 = 0 (the exception entry would be non-zero), x1 = the main thread's handle.
    const uint64_t entry = kModules[0].base;
    ctx->x[0] = 0;
    ctx->x[1] = h;
    ctx->x[30] = 0;
    NXLOG_I("boot", "entering %s at 0x%llx (x1 = main thread handle 0x%x)", kModules[0].file, static_cast<unsigned long long>(entry), h);
    nxrt::dispatch_call(ctx, entry);

    NXLOG_I("boot", "the entry function returned (x0 = 0x%llx): ending the process", static_cast<unsigned long long>(ctx->x[0]));
    nxrt::kernel::main_thread_release();
    nxrt::shutdown();
    return static_cast<int>(ctx->x[0] & 0xff);
}
