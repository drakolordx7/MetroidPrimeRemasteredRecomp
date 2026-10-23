// How much CPU does a thread get on a processor that six normal-priority spinners hold, when it works 1 ms and then yields (SwitchToThread / Sleep(0) / nothing)?
//   yield_demo <cpu> <class: normal|high> <seconds>
#include <windows.h>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>

static double now_ms() {
    LARGE_INTEGER f, c;
    QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&c);
    return 1000.0 * c.QuadPart / f.QuadPart;
}

int main(int argc, char** argv) {
    const int cpu = argc > 1 ? atoi(argv[1]) : 14;
    const bool high = argc > 2 && !strcmp(argv[2], "high");
    const double secs = argc > 3 ? atof(argv[3]) : 4.0;
    SetPriorityClass(GetCurrentProcess(), high ? HIGH_PRIORITY_CLASS : NORMAL_PRIORITY_CLASS);
    std::atomic<bool> stop{false};
    struct Case { const char* name; int prio; int mode; };
    const Case cases[] = {
        {"LOWEST   + SwitchToThread", THREAD_PRIORITY_LOWEST, 0},
        {"LOWEST   + Sleep(0)", THREAD_PRIORITY_LOWEST, 1},
        {"LOWEST   + no yield", THREAD_PRIORITY_LOWEST, 2},
        {"NORMAL   + SwitchToThread", THREAD_PRIORITY_NORMAL, 0},
        {"HIGHEST  + SwitchToThread", THREAD_PRIORITY_HIGHEST, 0},
        {"TIMECRIT + SwitchToThread", THREAD_PRIORITY_TIME_CRITICAL, 0},
        {"TIMECRIT + no yield", THREAD_PRIORITY_TIME_CRITICAL, 2},
    };
    for (const Case& c : cases) {
        std::atomic<double> done{0};
        std::atomic<bool> run{true};
        std::thread t([&] {
            SetThreadAffinityMask(GetCurrentThread(), 1ull << cpu);
            SetThreadPriority(GetCurrentThread(), c.prio);
            SetThreadPriorityBoost(GetCurrentThread(), TRUE);
            double cpu_ms = 0;
            while (run.load()) {
                const double t0 = now_ms();
                volatile unsigned long long x = 0;
                while (now_ms() - t0 < 1.0) x += 1;     // ~1 ms of work (wall time while running; it may be preempted inside)
                if (c.mode == 0) SwitchToThread();
                else if (c.mode == 1) Sleep(0);
                cpu_ms += 1.0;
                done.store(cpu_ms);
            }
        });
        Sleep(static_cast<DWORD>(secs * 1000));
        run = false;
        t.join();
        std::printf("%-28s %7.0f iterations of 1 ms in %.1f s\n", c.name, done.load(), secs);
    }
    return 0;
}
