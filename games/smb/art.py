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
            elif (line.startswith("#") and not line.startswith("##")) or name is None:
                continue
            elif line.strip() or out[name]:
                out[name].append(line.rstrip("\r"))
    for k in out:
        while out[k] and not out[k][-1].strip():
            out[k].pop()
    from games.smb import bg_art
    for k, f in bg_art.CODE.items():
        out.setdefault(k, f())
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
    if name in OWN:
        return OWN[name]()
    if s is None:                                   # own / glyph: free drawing
        return np.where(parse(art.get(name, []), w, h) == 255, 0, parse(art.get(name, []), w, h))
    if "uniform" in s:
        return np.concatenate([np.full((8, 8), v, np.uint8) for v in s["uniform"]], axis=1)
    base = baseline(s)
    if name not in art:
        return base
    rows = [r for r in art[name] if not r.startswith("!")]
    a = parse(rows, w, h)
    sil = base > 0
    out = np.where((a == 255) | (a == 0), base, a)
    for d in (r for r in art[name] if r.startswith("!")):
        k = d[1:].split()
        if k[0] == "outline":                       # !outline <colour> [nobottom] [notop] [noleft] [noright] [inner]
            pad = np.pad(sil, 1, constant_values="inner" in k)
            if "inner" not in k:
                if "nobottom" in k:
                    pad[-1, :] = True
                if "notop" in k:
                    pad[0, :] = True
                if "noleft" in k:
                    pad[:, 0] = True
                if "noright" in k:
                    pad[:, -1] = True
            edge = sil & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
            out = np.where(edge, int(k[1]), out)
        elif k[0] == "edge":                        # !edge <colour> <dirs from l r t b>: pixels whose neighbour that way is empty
            pad = np.pad(sil, 1, constant_values=False)
            nb = {"t": pad[:-2, 1:-1], "b": pad[2:, 1:-1], "l": pad[1:-1, :-2], "r": pad[1:-1, 2:]}
            for d_ in k[2]:
                out = np.where(sil & ~nb[d_], int(k[1]), out)
    return np.where(sil, out, 0).astype(np.uint8)


# 3x6 numerals for the score popups (own design; a tile holds two of them)
_NUM = {"0": "111 101 101 101 101 111", "1": "010 110 010 010 010 111", "2": "111 001 111 100 100 111",
        "4": "101 101 101 111 001 001", "5": "111 100 111 001 001 111", "8": "111 101 111 101 101 111",
        "U": "101 101 101 101 101 111", "P": "111 101 111 100 100 100", " ": "000 000 000 000 000 000"}


def _numerals(text, colour=2):
    out = np.zeros((8, 4 * len(text)), np.uint8)
    for i, ch in enumerate(text):
        for y, r in enumerate(_NUM[ch].split()):
            for x, c in enumerate(r):
                if c == "1":
                    out[1 + y, 4 * i + x] = colour
    return out


OWN = {
    "score_100_8000": lambda: _numerals("10204050800 "),      # 100 = "10" + "0 ", 1000 = "10" + "00"
    "score_00": lambda: _numerals("00"),
    "score_1up": lambda: _numerals("1UP "),
}


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
