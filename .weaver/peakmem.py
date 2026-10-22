"""Run a command in a Windows job object; report wall time, CPU time of the process tree, the peak committed memory of the
job (all processes together) and of its largest process, the system RAM in use at start / peak, and the lowest free disk.
    python .weaver/peakmem.py [--drive D:/] -- <command...>        (set MSYS2_ARG_CONV_EXCL='*' under git bash)"""
import os, sys, time, shutil, subprocess, ctypes
from ctypes import wintypes as W

k32 = ctypes.windll.kernel32

class MS(ctypes.Structure):
    _fields_ = [('l', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in ('tp', 'ap', 'tpf', 'apf', 'tv', 'av', 'ae')]

class BASIC(ctypes.Structure):
    _fields_ = [('PerProcessUserTimeLimit', ctypes.c_longlong), ('PerJobUserTimeLimit', ctypes.c_longlong), ('LimitFlags', W.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t), ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', W.DWORD),
                ('Affinity', ctypes.c_size_t), ('PriorityClass', W.DWORD), ('SchedulingClass', W.DWORD)]

class IOC(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ('a', 'b', 'c', 'd', 'e', 'f')]

class EXT(ctypes.Structure):
    _fields_ = [('Basic', BASIC), ('Io', IOC), ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]

class ACCT(ctypes.Structure):
    _fields_ = [(n, ctypes.c_longlong) for n in ('TotalUserTime', 'TotalKernelTime', 'u', 'k')] + [(n, W.DWORD) for n in ('pf', 'tp', 'ap', 'tt')]

def used():
    m = MS(); m.l = ctypes.sizeof(m); k32.GlobalMemoryStatusEx(ctypes.byref(m))
    return (m.tp - m.ap) / 2**30, m.tp / 2**30

def main():
    a = sys.argv[1:]
    drive = 'D:/'
    if a and a[0] == '--drive':
        drive, a = a[1], a[2:]
    if a and a[0] == '--':
        a = a[1:]
    base, total = used()
    k32.CreateJobObjectW.restype = W.HANDLE
    job = k32.CreateJobObjectW(None, None)
    t0 = time.time()
    p = subprocess.Popen(a)
    k32.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]; k32.CreateJobObjectW.restype = W.HANDLE
    ok = k32.AssignProcessToJobObject(job, int(p._handle))
    if not ok: print("PEAKMEM: AssignProcessToJobObject failed", ctypes.get_last_error() or k32.GetLastError())
    peak, freemin = base, shutil.disk_usage(drive).free
    while p.poll() is None:
        peak = max(peak, used()[0]); freemin = min(freemin, shutil.disk_usage(drive).free)
        time.sleep(0.5)
    e = EXT(); k32.QueryInformationJobObject(job, 9, ctypes.byref(e), ctypes.sizeof(e), None)
    ac = ACCT(); k32.QueryInformationJobObject(job, 1, ctypes.byref(ac), ctypes.sizeof(ac), None)
    print('PEAKMEM exit=%d wall=%.1fs cpu=%.0fs job_peak_commit=%.2fGB biggest_process_peak=%.2fGB system_ram_used base=%.1fGB peak=%.1fGB of %.0fGB disk_free_min=%.1fGB'
          % (p.returncode, time.time() - t0, (ac.TotalUserTime + ac.TotalKernelTime) / 1e7, e.PeakJobMemoryUsed / 2**30,
             e.PeakProcessMemoryUsed / 2**30, base, peak, total, freemin / 2**30))
    return p.returncode

sys.exit(main())
