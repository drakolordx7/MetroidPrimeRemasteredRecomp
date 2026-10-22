#!/usr/bin/env python3
"""Align our screenshots (dir A) to the best-matching Eden frames (dir B).

Thumbnail MAE (96x54 grey, BOX) + monotonic DTW picks one B frame per A frame
(B index non-decreasing as A increases). Writes OUT_DIR/<a>_<b>.png side-by-side
(ours | Eden | diff x4) and OUT_DIR/align.tsv with full-res imgdiff metrics.

Usage: python .weaver\\align_frames.py A_DIR B_DIR OUT_DIR [--amin N] [--bmin N] [--bmax M] [--mask hud]
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, r"D:\AI\Active\Metroid-Prime\tools\test")
import imgdiff  # noqa: E402

THUMB = (96, 54)
PANEL = (640, 360)


def load_dir(d):
    """{frame_number: path} for every numeric-named PNG in d."""
    out = {}
    for p in glob.glob(os.path.join(d, "*.png")):
        stem = os.path.splitext(os.path.basename(p))[0]
        if stem.isdigit():
            out[int(stem)] = p
    return out


def thumb(path):
    with Image.open(path) as im:
        return np.asarray(im.convert("L").resize(THUMB, Image.Resampling.BOX), dtype=np.float64)


def match_monotone(C):
    """C[i, j] = cost of A[i] vs B[j]. Returns one j per i, non-decreasing in i, minimal total cost."""
    n, m = C.shape
    D = np.zeros((n, m))
    prev = np.zeros((n, m), dtype=np.int64)
    D[0] = C[0]
    for i in range(1, n):
        best, arg = np.inf, -1
        for j in range(m):
            if D[i - 1, j] < best:
                best, arg = D[i - 1, j], j
            D[i, j] = C[i, j] + best
            prev[i, j] = arg
    j = int(np.argmin(D[n - 1]))
    path = [j]
    for i in range(n - 1, 0, -1):
        j = int(prev[i, j])
        path.append(j)
    return path[::-1]


def side_by_side(a_path, b_path, a_n, b_n, out_path):
    pa = Image.open(a_path).convert("RGB").resize(PANEL, Image.Resampling.LANCZOS)
    pb = Image.open(b_path).convert("RGB").resize(PANEL, Image.Resampling.LANCZOS)
    diff = np.abs(np.asarray(pa, dtype=np.int16) - np.asarray(pb, dtype=np.int16))
    amp = Image.fromarray(np.clip(diff * 4, 0, 255).astype(np.uint8))
    canvas = Image.new("RGB", (PANEL[0] * 3, PANEL[1]))
    draw = ImageDraw.Draw(canvas)
    for k, (im, label) in enumerate([(pa, f"ours {a_n}"), (pb, f"Eden {b_n}"), (amp, "diff x4")]):
        x0 = k * PANEL[0]
        canvas.paste(im, (x0, 0))
        x, y = x0 + 8, 8
        box = draw.textbbox((x, y), label)
        draw.rectangle((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4), fill=(0, 0, 0))
        draw.text((x, y), label, fill=(255, 255, 0))
    canvas.save(out_path)


def full_metrics(a_path, b_path, mask):
    with Image.open(a_path) as im:
        size = im.size  # native resolution of ours; Eden is resampled to it by imgdiff
    r = imgdiff.compare(a_path, b_path, masks=mask, size=size)
    return r.ssim, r.mae, r.hist_corr, r.changed_frac


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a_dir")
    ap.add_argument("b_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--amin", type=int, default=None, help="only A frames >= N")
    ap.add_argument("--bmin", type=int, default=None)
    ap.add_argument("--bmax", type=int, default=None)
    ap.add_argument("--mask", default=None, help="imgdiff mask preset or x0,y0,x1,y1 (metrics only)")
    args = ap.parse_args()

    A = load_dir(args.a_dir)
    B = load_dir(args.b_dir)
    ta = {n: thumb(p) for n, p in A.items()}
    tb = {n: thumb(p) for n, p in B.items()}

    a_nums = sorted(n for n in A if args.amin is None or n >= args.amin)
    b_nums = sorted(n for n in B
                    if (args.bmin is None or n >= args.bmin) and (args.bmax is None or n <= args.bmax))
    if not a_nums or not b_nums:
        sys.exit("error: no A or B frames in the requested range")

    C = np.array([[np.abs(ta[a] - tb[b]).mean() for b in b_nums] for a in a_nums])
    path = match_monotone(C)
    raw = np.argmin(C, axis=1)
    mask = [args.mask] if args.mask else None

    os.makedirs(args.out_dir, exist_ok=True)
    rows = []
    for i, a in enumerate(a_nums):
        b = b_nums[path[i]]
        a_s, b_s = f"{a:06d}", f"{b:06d}"
        side_by_side(A[a], B[b], a_s, b_s, os.path.join(args.out_dir, f"{a_s}_{b_s}.png"))
        ssim, mae, hist, changed = full_metrics(A[a], B[b], mask)
        rows.append((a_s, b_s, C[i, path[i]], ssim, mae, hist, changed))
        print(f"{a_s} -> {b_s}  ssim={ssim:.4f} mae={mae:.2f} (thumb {C[i, path[i]]:.2f}, "
              f"raw argmin {b_nums[raw[i]]:06d})")

    tsv = os.path.join(args.out_dir, "align.tsv")
    with open(tsv, "w", encoding="utf-8") as f:
        f.write("a\tb\tthumb_mae\tssim\tmae\thist_corr\tchanged_frac\n")
        for a_s, b_s, t, s, m, h, c in rows:
            f.write(f"{a_s}\t{b_s}\t{t:.4f}\t{s:.5f}\t{m:.4f}\t{h:.5f}\t{c:.5f}\n")

    ssims = np.array([r[3] for r in rows], dtype=np.float64)
    maes = np.array([r[4] for r in rows], dtype=np.float64)
    print(f"count={len(rows)} median_ssim={np.nanmedian(ssims):.4f} median_mae={np.nanmedian(maes):.3f}")
    print(f"wrote {tsv}")


if __name__ == "__main__":
    main()
