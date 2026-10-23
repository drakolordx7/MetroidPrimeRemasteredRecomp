"""Audio measurement run (real XAudio2 sink at volume 0, WAV dump of every frame sent to the sink).

Script = title -> New Game -> Frigate hangar (gameplay.prologue), then 200 s of game time, then pass.
One mpr.exe process, default real-time clock (NXRT_TIME_MODE is not set), same launch as tools/test/phys_table.py
(headless, shader + bc7 caches, NXRT_FS_* paths, watchdog), plus the audio variables.

  tools\\.venv\\Scripts\\python .weaver\\audio_run.py            run
  tools\\.venv\\Scripts\\python .weaver\\audio_run.py --dry-run  write script.nxs only, print it

Output (work/run_play3_audio/out): mpr.log, script.nxs, audio.wav, out/trace.jsonl, out/result.json,
stdout.txt, stderr.txt, timing.json (wall-clock start/end of the process, exit code).
Exit code: the game's exit code (124 = killed by the wall limit).
"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools', 'test'))
import gameplay as gp  # noqa: E402

ROOT = gp.ROOT
EXE_DIR = os.path.join(ROOT, 'work', 'run_play3_audio', 'exe')
OUT = os.path.join(ROOT, 'work', 'run_play3_audio', 'out')
SHADERS = ROOT + '/work/shader_cache/spirv'
BC7 = ROOT + '/work/bc7_cache_polish'
GAME_SECONDS = 200
WALL_LIMIT = 900          # NXRT_TEST_WALL_TIMEOUT_S and --max-seconds


def script():
    return (['# audio run: title -> New Game -> Frigate hangar, then %d s of game time, then pass' % GAME_SECONDS]
            + gp.prologue(timeout_ms=600000)
            + ['@hash gameplay_window_start', '@run %d' % GAME_SECONDS, '@hash gameplay_window_end', '@pass', ''])


def launch(lines):
    os.makedirs(OUT, exist_ok=True)
    cwd = os.path.join(OUT, 'cwd')
    os.makedirs(cwd, exist_ok=True)
    cache = os.path.join(cwd, 'bc7_cache')
    if not os.path.exists(cache):
        src = os.path.normpath(os.path.join(ROOT, 'work', 'run', 'bc7_cache'))
        subprocess.run('mklink /J "%s" "%s"' % (os.path.normpath(cache), src), shell=True, capture_output=True)
    script_path = os.path.join(OUT, 'script.nxs')
    open(script_path, 'w').write('\n'.join(lines) + '\n')

    e = dict(os.environ)
    for k in ('NXRT_TIME_MODE', 'NXRT_TEST_DETERMINISTIC', 'NXRT_TEST_CLOCK_STEP_TICKS'):   # real-time clock: none of these set
        e.pop(k, None)
    e.update(NXRT_TEST_SCRIPT=script_path, NXRT_TEST_OUT=os.path.join(OUT, 'out'),
             NXRT_TEST_REGIONS=ROOT + '/tools/test/regions.tsv', NXRT_BOOT_GFX='headless',
             NXRT_FS_ROMFS=ROOT + '/game/romfs', NXRT_FS_SAVE_DIR=os.path.join(cwd, 'save'),
             NXRT_TEST_WALL_TIMEOUT_S=str(WALL_LIMIT), NXRT_DIAG_WATCHDOG_SECONDS='60',
             NXRT_NVN_SHADER_CACHE=SHADERS, NXRT_NVN_BC7_CACHE=BC7, NXRT_GFX_HEADLESS='1',
             NXRT_AUDIO_SINK='xaudio2', NXRT_AUDIO_VOLUME='0',
             NXRT_AUDIO_WAV_DUMP=os.path.join(OUT, 'audio.wav'))
    cmd = [EXE_DIR + '/mpr.exe', '--log', os.path.join(OUT, 'mpr.log'), '--max-seconds', str(WALL_LIMIT)]
    with open(os.path.join(OUT, 'stdout.txt'), 'w') as so, open(os.path.join(OUT, 'stderr.txt'), 'w') as se:
        t_start = time.time()
        try:
            rc = subprocess.run(cmd, cwd=cwd, env=e, stdout=so, stderr=se, timeout=WALL_LIMIT + 60).returncode
        except subprocess.TimeoutExpired:
            rc = 124
        t_end = time.time()
    timing = dict(exit=rc, wall_start=t_start, wall_end=t_end, wall_s=t_end - t_start,
                  wall_start_iso=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t_start)),
                  wall_end_iso=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t_end)),
                  cmd=cmd, env_audio={k: e[k] for k in ('NXRT_AUDIO_SINK', 'NXRT_AUDIO_VOLUME', 'NXRT_AUDIO_WAV_DUMP')},
                  time_mode_set='NXRT_TIME_MODE' in e)
    json.dump(timing, open(os.path.join(OUT, 'timing.json'), 'w'), indent=1)
    return timing


def main():
    lines = script()
    if '--dry-run' in sys.argv:
        print('\n'.join(lines))
        return 0
    t = launch(lines)
    print(json.dumps(t, indent=1))
    return t['exit']


if __name__ == '__main__':
    sys.exit(main())
