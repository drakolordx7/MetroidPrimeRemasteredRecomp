"""S13: summarise the player rows of a scripted run: python .weaver/vtrace.py DIR [--step 0.5] [--area PREFIX]  (one row per STEP seconds of game time)"""
import json, argparse
ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--area', default=''); ap.add_argument('--step', type=float, default=0.5)
a = ap.parse_args()
last = -1e9; lastarea = None
for l in open(a.dir.rstrip('/') + '/out/trace.jsonl'):
    try: r = json.loads(l)
    except ValueError: continue
    if 'pos' not in r or not r['area'].startswith(a.area): continue
    if r['area'] != lastarea: print('-- area', r['area'][:8]); lastarea = r['area']; last = -1e9
    if r['igt'] - last >= a.step:
        last = r['igt']
        print('f%d igt %.2f pos %s spd %.1f yaw %.3f pit %.3f | cam yaw %.3f pit %.3f | st %s cs %s mo %s or %s b %s vis %s msl %s ms %.0f' % (
            r['f'], r['igt'], [round(x, 1) for x in r['pos']], r.get('spd', -1), r['yaw'], r.get('pitch', 0), r.get('camyaw', 0), r.get('campitch', 0),
            r['state'], r.get('cam'), r.get('morph'), r.get('orbit'), r.get('beam'), r.get('visor'), r.get('msl'), r.get('ms', 0)))
