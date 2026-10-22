"""First-boot loop for mpr.exe: rebuild what changed, run headless with a timeout, print the tail of the log and a summary of every
unknown call (SVC, IPC command, NVN function, HLE stub), the stop reason and the guest call stack (demangled).

  tools\\.venv\\Scripts\\python tools\\boot\\boot.py [options]

  --seconds N     wall-clock limit for the run (default 40); mpr.exe is also given --max-seconds N-2 so it dumps its state first
  --tail N        last N log lines to print (default 30)
  --libs          also rebuild the lifted game libraries (recomp\\scripts\\build_mpr.cmd, ~2 min, incremental)
  --no-build      run the existing mpr.exe
  --level L       NXRT_LOG_LEVEL for the run (info|debug|trace)
  --link M        [boot] link: rtld (default; the game's own dynamic linker relocates) | host (the runtime's linker)
  --probe P       no-sdk-services: skip nninitInitializeSdkModule so the boot reaches nnMain without the Horizon services
  --stub-result R  Result every stub IPC command answers (0 = succeed with an empty reply), to see the next service the game asks for
  --env K=V       extra environment variable (repeatable), e.g. --env NXRT_SVC_UNKNOWN_LOG_LIMIT=1000
  --grep RE       also print every log line matching RE (case-insensitive)
  --log-only      do not run; summarise work\\run\\mpr.log from the last run

Runs in work\\run (log work\\run\\mpr.log, previous log mpr.log.prev). Exit code: the exit code of mpr.exe (124 = deadline, 3/4 = crash).
"""
import argparse, os, re, subprocess, sys, shutil, time, collections

ROOT = r'D:\AI\Active\Metroid-Prime'
RUN = os.path.join(ROOT, 'work', 'run_nvn3')
EXE = os.path.join(os.environ.get('MPR_BUILD_DIR') or os.path.join(ROOT, 'game-build', 'build', 'release'), 'mpr.exe')   # MPR_RUNTIME / MPR_BUILD_DIR: build against another runtime checkout (game-build/scripts/build.ps1)
CXXFILT = r'C:\Program Files\LLVM\bin\llvm-cxxfilt.exe'
sys.path.insert(0, os.path.join(ROOT,'tools','boot'))
import addrname


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, **kw)


def demangle(text):
    names = set(re.findall(r'\b_Z[A-Za-z0-9_$.]+', text))
    if not names or not os.path.exists(CXXFILT):
        return text
    try:
        out = subprocess.run([CXXFILT] + sorted(names), capture_output=True, text=True, timeout=30).stdout.splitlines()
        if len(out) == len(names):
            for n, d in zip(sorted(names), out):
                text = text.replace(n, d)
    except Exception:
        pass
    return text


def build(libs):
    if libs:
        print('== game libraries (recomp\\scripts\\build_mpr.cmd)')
        r = sh(os.path.join(ROOT, 'recomp', 'scripts', 'build_mpr.cmd'), cwd=ROOT, capture_output=True, text=True)
        print((r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else '(no output)')
        if r.returncode:
            print('LIBRARY BUILD FAILED'); print((r.stdout + r.stderr)[-3000:]); sys.exit(10)
    print('== mpr.exe (game-build\\scripts\\build.ps1)')
    t = time.time()
    r = sh('pwsh -NoProfile -File "%s"' % os.path.join(ROOT, 'game-build-nvn3', 'scripts', 'build.ps1'), cwd=ROOT, capture_output=True, text=True,
           env=dict(os.environ, MSYS2_ARG_CONV_EXCL='*'))
    out = r.stdout + r.stderr
    errs = [l for l in out.splitlines() if ' error' in l or 'error:' in l or 'FAILED' in l or 'undefined symbol' in l]
    if r.returncode:
        print('BUILD FAILED'); print('\n'.join(errs[:30]) or out[-3000:]); sys.exit(11)
    print('built in %.0fs' % (time.time() - t))


def run(a):
    os.makedirs(RUN, exist_ok=True)
    log = os.path.join(RUN, 'mpr.log')
    env = dict(os.environ)
    # the run directory is work\run, so point the services at the real RomFS and a disposable save folder
    env.setdefault('NXRT_FS_ROMFS', os.path.join(ROOT, 'game', 'romfs'))
    env.setdefault('NXRT_FS_SAVE_DIR', os.path.join(RUN, 'save'))
    if a.level:
        env['NXRT_LOG_LEVEL'] = a.level
    if a.probe: env['NXRT_BOOT_PROBE'] = a.probe
    if a.stub_result: env['NXRT_IPC_STUB_RESULT'] = a.stub_result
    for kv in a.env or []:
        k, v = kv.split('=', 1); env[k] = v
    cmd = [EXE, '--log', log, '--max-seconds', str(max(1, a.seconds - 2)), '--link', a.link]
    print('== run (%ds limit): %s' % (a.seconds, ' '.join(cmd[1:])))
    t = time.time()
    p = subprocess.Popen(cmd, cwd=RUN, env=env, stdout=open(os.path.join(RUN, 'run.out'), 'w'), stderr=subprocess.STDOUT)
    try:
        rc = p.wait(timeout=a.seconds)
    except subprocess.TimeoutExpired:
        p.kill(); rc = 124
        print('(killed at the host deadline)')
    print('exit code %d after %.1fs' % (rc, time.time() - t))
    return rc


def summarise(a):
    log = os.path.join(RUN, 'mpr.log')
    lines = open(log, errors='replace').read().splitlines()
    text = '\n'.join(lines)
    print('\n== summary of %s (%d lines)' % (log, len(lines)))
    # stop reason
    stop = [l for l in lines if re.search(r'HOST EXCEPTION|GUEST TRAP|svcBreak reason|svcExitProcess|uncaught C\+\+|max_seconds reached|returned \(x0|FREEZE|freeze', l)]
    print('-- stop:')
    for l in stop[:6]: print('  ' + addrname.annotate(l[:300]))
    m = re.search(r'guest call stack \(innermost first\): (.*)', text)
    bt = [l for l in lines if 'guest backtrace' in l or 'guest frame chain' in l]
    if m:
        print('-- guest call stack (innermost first):')
        for f in m.group(1).split()[:14]: print('  ' + addrname.annotate(f))
    for l in bt[:3]: print('  ' + addrname.annotate(l[:500]))
    # unknown svc
    unk = collections.OrderedDict()
    for l in lines:
        mm = re.search(r'UNKNOWN SVC (0x[0-9A-Fa-f]+) \((\w+)\) #(\d+) (x0=.*?) caller', l)
        if mm: unk.setdefault((mm.group(1), mm.group(2)), [0, mm.group(4)])[0] = int(mm.group(3))
    print('-- unknown SVCs: %s' % ('none' if not unk else ''))
    for (n, nm), (c, args) in unk.items(): print('  %s %s x%d first %s' % (n, nm, c, args[:150]))
    # stub services
    st = collections.OrderedDict()
    for l in lines:
        mm = re.search(r'STUB SERVICE (\S+) cmd (\d+) \((.*?)\)', l)
        if mm: st.setdefault((mm.group(1), int(mm.group(2))), [0, mm.group(3)])[0] += 1
    sm = [re.search(r'GetServiceHandle\((\S+)\)', l).group(1) for l in lines if 'GetServiceHandle(' in l]
    print('-- services requested: %s' % (', '.join(collections.OrderedDict.fromkeys(sm)) or 'none'))
    print('-- stub service commands: %s' % ('none' if not st else ''))
    for (s, c), (n, d) in st.items(): print('  %s cmd %d (logged x%d) %s' % (s, c, n, d[:120]))
    # nvn and hle stubs
    nvn = collections.OrderedDict()
    for l in lines:
        mm = re.search(r'nvn: STUB (\w+)\(|nvn: UNKNOWN NVN PROC (\w+)\(', l)
        if mm: nvn.setdefault(mm.group(1) or mm.group(2), l[:260])
    print('-- NVN functions hit: %s' % ('none' if not nvn else ''))
    for k, v in list(nvn.items())[:40]: print('  ' + v)
    hle = [l for l in lines if 'shell installed' not in l and re.search(r'logging stub|has no host implementation|UNKNOWN NVN PROC|hle stub called', l)]
    print('-- HLE / import stubs: %s' % ('none' if not hle else ''))
    for l in hle[:20]: print('  ' + l[:260])
    warn = collections.Counter(re.sub(r'0x[0-9a-fA-F]+|\d+', 'N', re.sub(r'^\[[^\]]*\] ', '', l))[:140] for l in lines if re.match(r'\[[^\]]* W ', l))
    print('-- warnings (distinct, with counts): %s' % ('none' if not warn else ''))
    for k, c in warn.most_common(12): print('  x%d %s' % (c, k))
    if a.grep:
        print('-- grep %r:' % a.grep)
        for l in [l for l in lines if re.search(a.grep, l, re.I)][:60]: print('  ' + l[:300])
    print('\n== last %d lines' % a.tail)
    print(demangle('\n'.join(l[:300] for l in lines[-a.tail:])))


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--seconds', type=int, default=40)
    ap.add_argument('--tail', type=int, default=30)
    ap.add_argument('--libs', action='store_true')
    ap.add_argument('--no-build', action='store_true')
    ap.add_argument('--level')
    ap.add_argument('--link', default='rtld')
    ap.add_argument('--env', action='append')
    ap.add_argument('--grep')
    ap.add_argument('--probe', help='[boot] probe: no-sdk-services = run nn::init::Start step by step without nninitInitializeSdkModule (reaches nnMain)')
    ap.add_argument('--stub-result', help='[ipc] stub_result: Result every stub service command answers (0 = succeed with an empty reply)')
    ap.add_argument('--log-only', action='store_true')
    ap.add_argument('-h', '--help', action='store_true')
    a = ap.parse_args()
    if a.help:
        print(__doc__); return 0
    rc = 0
    if not a.log_only:
        if not a.no_build: build(a.libs)
        rc = run(a)
    summarise(a)
    return rc


if __name__ == '__main__':
    sys.exit(main())
