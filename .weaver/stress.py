"""Burn CPU on N cores for S seconds (audio timing under load): python stress.py [N] [S]"""
import multiprocessing, sys, time

def burn(t):
    end = time.time() + t
    x = 0
    while time.time() < end:
        x += 1

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    t = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    ps = [multiprocessing.Process(target=burn, args=(t,)) for _ in range(n)]
    [p.start() for p in ps]
    [p.join() for p in ps]
