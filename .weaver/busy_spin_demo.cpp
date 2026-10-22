#include <windows.h>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <thread>
int main(int argc, char** argv) {
    bool yield = argc > 1;
    std::atomic<uint32_t> word{1};
    std::atomic<bool> ready{false}, acq{false};
    const DWORD_PTR cpu = DWORD_PTR(1) << 21;
    std::thread holder([&] {
        SetThreadAffinityMask(GetCurrentThread(), cpu);
        SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_LOWEST);
        SetThreadPriorityBoost(GetCurrentThread(), TRUE);
        ready = true;
        volatile uint64_t s = 0;
        auto until = std::chrono::steady_clock::now() + std::chrono::milliseconds(300);
        while (std::chrono::steady_clock::now() < until) s += 1;
        word.store(0);
    });
    while (!ready) Sleep(1);
    auto t0 = std::chrono::steady_clock::now();
    std::thread waiter([&] {
        SetThreadAffinityMask(GetCurrentThread(), cpu);
        SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_HIGHEST);
        SetThreadPriorityBoost(GetCurrentThread(), TRUE);
        for (uint32_t spins = 0;; spins++) {
            uint32_t e = 0;
            if (word.load() == 0 && word.compare_exchange_weak(e, 1)) break;
            if (yield) { if (spins < 64) YieldProcessor(); else if (spins < 20000) SwitchToThread(); else Sleep(1); }
        }
        acq = true;
    });
    while (!acq && std::chrono::steady_clock::now() - t0 < std::chrono::seconds(60)) Sleep(5);
    printf("%s: acquired=%d after %.2f s\n", yield ? "yielding" : "pure spin", (int)acq.load(), std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count());
    if (!acq) word.store(0);
    holder.join(); waiter.join();
}
