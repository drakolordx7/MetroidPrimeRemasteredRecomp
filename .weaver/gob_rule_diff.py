"""Count game TXTRs whose level-0 block height differs between tools/tiling default_gob_blocks_y and the tegra_swizzle crate rule (what retrotool/the game's data use)."""
import csv, sys, collections
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\tools\survey')
from txtr_tally import fmt_info
def default(r):
    g = 1
    while g < 16 and g * 8 < r: g <<= 1
    return g
def crate(r):
    hh = r + r // 2
    return 16 if hh >= 128 else 8 if hh >= 64 else 4 if hh >= 32 else 2 if hh >= 16 else 1
tot = diff = 0; ex = collections.Counter()
for row in csv.DictReader(open(r'D:\AI\Active\Metroid-Prime\work\survey\textures\txtr_all.tsv'), delimiter='\t'):
    if row['kind'] == '3D': continue
    bw, bh, bpb, fam, srgb = fmt_info(row['fmt'])
    rows = -(-int(row['h']) // bh)
    tot += 1
    if default(rows) != crate(rows):
        diff += 1; ex[(row['fmt'], row['w'], row['h'])] += 1
print('non-3D textures', tot, 'differ', diff)
for k, v in ex.most_common(12): print(k, v)
