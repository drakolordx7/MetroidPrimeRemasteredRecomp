"""Fraction of 16x16 blocks that look like colour noise (strong horizontal gradients whose R,G,B parts are uncorrelated): python .weaver/noisescore.py img.png ..."""
import sys, numpy as np
from PIL import Image
def noise_score(path, blk=16):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32)
    h, w, _ = a.shape; h -= h % blk; w -= w % blk
    d = np.abs(np.diff(a[:h, :w], axis=1))[:, :w - 1 - ((w - 1) % blk) if False else None]
    dx = np.diff(a[:h, :w], axis=1)                       # h x (w-1) x 3
    dx = dx[:, :w - blk if False else (w // blk) * blk - 0 if False else dx.shape[1]]
    ww = (dx.shape[1] // blk) * blk
    dx = dx[:, :ww]
    B = dx.reshape(h // blk, blk, ww // blk, blk, 3).transpose(0, 2, 1, 3, 4).reshape(h // blk, ww // blk, blk * blk, 3)
    mag = np.abs(B).mean(axis=(2, 3))
    r, g, b = B[..., 0], B[..., 1], B[..., 2]
    def corr(x, y):
        xm = x - x.mean(axis=2, keepdims=True); ym = y - y.mean(axis=2, keepdims=True)
        den = np.sqrt((xm ** 2).sum(axis=2) * (ym ** 2).sum(axis=2)) + 1e-6
        return (xm * ym).sum(axis=2) / den
    c = np.minimum(corr(r, g), corr(g, b))
    noisy = (mag > 30) & (c < 0.5)
    return float(noisy.mean()), int(noisy.sum())
if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, noise_score(p))
