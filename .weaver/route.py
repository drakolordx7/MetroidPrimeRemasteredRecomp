"""S25 route: the scripted playthrough as steps on top of live.py (a game started with `live.py start` and `live.py newgame` is in control at the Frigate hangar).
  python route.py list | run STEP [STEP...]"""
import sys
sys.path.insert(0, 'D:/AI/Active/Metroid-Prime/.weaver')
import live as L

def shoot(x, y, z, n=1):
    L.aim(x, y, z)
    cmds = ['hold ZL', 'wait 25'] + ['press ZR for 8', 'wait 25'] * n + ['release ZL', 'wait 15']
    return L.send(cmds)

def hangar_field1():
    L.goto(82.8, -115.4)
    for x, y in ((73.9, 2.9), (73.9, 7.0), (91.8, 2.8), (91.8, 7.0)):
        shoot(x, y, -131.9)
    L.goto(82.8, -126)
    L.face(3.1416)
    return L.send(['stick left 0 1 for 200', 'wait 5'])

STEPS = {'hangar_field1': hangar_field1}

def hangar_scan_panel():
    L.goto(88.5, -162.5)
    L.face(1.55)
    L.send(['press RIGHT for 6', 'wait 30'])
    L.send(['mouse 100 125 for 1', 'wait 15', 'hold ZL', 'wait 200', 'release ZL', 'wait 10', 'press A for 6', 'wait 20', 'press UP for 6', 'wait 30', 'wait 700'])      # the scan starts a short cutscene
    return L.status()

def hangar_field2():
    L.goto(80, -167.7)
    for z in (-158.5, -177.0):
        for x, y in ((64.0, 0.3), (64.0, 4.6), (63.5, 14.2)):
            shoot(x, y, z)
    L.send(['mouse 0 900 for 1', 'wait 10'])          # level the view again after shooting the high lights
    L.goto(60, -167.7)
    L.face(-1.5708)
    return L.send(['stick left 0 1', 'wait 70', 'press B for 20', 'wait 60', 'stick left 0 0'])

STEPS.update({'hangar_scan_panel': hangar_scan_panel, 'hangar_field2': hangar_field2})

if __name__ == '__main__':
    if sys.argv[1] == 'list':
        print(' '.join(STEPS))
    else:
        for n in sys.argv[2:]:
            print(n, L.fmt(STEPS[n]()))
