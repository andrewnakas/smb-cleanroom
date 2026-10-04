"""Our pixel art: one index image (0..3) per atlas picture.

Sources, in order:
  1. `own` pictures (score popups, etc.): drawn freely by code here, no retail facts.
  2. art/*.txt: hand-drawn ASCII. A block is `@ name` followed by rows of
     `.` (transparent), `1 2 3` (colour index) or `?` / space (take the baseline).
  3. baseline: the kept coarse grid inside the kept silhouette.
Whatever the source, pictures with a kept silhouette are snapped to it: outside
is 0, inside is never 0 (unpainted pixels take the baseline colour).
"""
import glob
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_spec():
    return json.load(open(os.path.join(HERE, "spec", "pictures.json")))


def load_art():
    out = {}
    for f in sorted(glob.glob(os.path.join(HERE, "art", "*.txt"))):
        name = None
        for line in open(f, encoding="utf-8").read().split("\n"):
            if line.startswith("@"):
                name = line[1:].strip()
                out[name] = []
            elif line.startswith("#") or name is None:
                continue
            elif line.strip() or out[name]:
                out[name].append(line.rstrip("\r"))
    for k in out:
        while out[k] and not out[k][-1].strip():
            out[k].pop()
    return out


def baseline(s) -> np.ndarray:
    h, w = s["h"], s["w"]
    sil = np.array([[c == "#" for c in r] for r in s["sil"]])
    g = np.array(s["grid"])
    gh, gw = g.shape
    out = np.zeros((h, w), np.uint8)
    for gy in range(gh):
        for gx in range(gw):
            out[gy * h // gh:(gy + 1) * h // gh, gx * w // gw:(gx + 1) * w // gw] = g[gy, gx] or 1
    # empty-cell fallback already 1; mask to silhouette
    return np.where(sil, out, 0).astype(np.uint8)


def parse(rows, w, h) -> np.ndarray:
    """-> (h, w) of 0..3, 255 = unpainted"""
    out = np.full((h, w), 255, np.uint8)
    for y, r in enumerate(rows[:h]):
        for x, c in enumerate(r[:w]):
            if c == ".":
                out[y, x] = 0
            elif c in "123":
                out[y, x] = int(c)
    return out


def render(p, spec, art) -> np.ndarray:
    """atlas picture -> index image"""
    name = p["name"]
    h, w = len(p["layout"]) * 8, len(p["layout"][0]) * 8
    s = spec.get(name)
    if s is None:                                   # own / glyph: free drawing
        return np.where(parse(art.get(name, []), w, h) == 255, 0, parse(art.get(name, []), w, h))
    if "uniform" in s:
        return np.concatenate([np.full((8, 8), v, np.uint8) for v in s["uniform"]], axis=1)
    base = baseline(s)
    if name not in art:
        return base
    a = parse(art[name], w, h)
    sil = base > 0
    out = np.where((a == 255) | (a == 0), base, a)
    return np.where(sil, out, 0).astype(np.uint8)


def ascii_of(img, owned=None) -> str:
    """index image -> text; pixels of tiles this picture does not own are shown as `:` (empty) / `+` (set)"""
    rows = []
    for y in range(img.shape[0]):
        r = ""
        for x in range(img.shape[1]):
            v = img[y, x]
            if owned is not None and not owned[y // 8][x // 8]:
                r += "+" if v else ":"
            else:
                r += ".123"[v]
        rows.append(r)
    return "\n".join(rows)
