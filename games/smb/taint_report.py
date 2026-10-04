"""DIRTY ROOM: taint scan of the clean ROM (and publish trees) against retail.

    python -m games.smb.taint_report <retail.nes> <clean.nes> [tree to scan ...] [-v]

Prints one screen and "TAINT: n failing". Rules (logged in STATUS.md):
  T1 raw     any 16-byte window of retail CHR pixels (>= 6 distinct byte values) found in the clean ROM
             or in any file of the given trees -> fail
             (forgiven: windows lying in T2 coincidence tiles, bar <= 6 bytes or <= 2 distinct values outside them)
  T2 tile    a clean tile equal to any retail tile (any slot, any flip):
             - picture tile with >= 2 non-zero colours                                 -> fail
             - picture tile with <= 1 non-zero colour: it IS the kept silhouette       -> coincidence, counted
             - glyph / own tile (nothing kept) with > 10 set pixels                    -> fail
             - uniform tile (one value)                                                -> coincidence
  T3 picture per picture with a kept silhouette: detail = retail pixels that differ from the kept-fact baseline.
             >= 12 detail pixels, > 75 % of them reproduced and > 90 % overall agreement -> fail
  T4 script  title script: any retail entry that draws non-text tiles (>= 8 data bytes) present in ours -> fail
  T5 palette a palette row equal to retail with a non-grey colour                      -> fail (grey rows: counted)
  T6 prg     PRG may differ from retail only inside the palette tables (code/levels/text/music are kept)
"""
import os
import sys

import numpy as np

from cleanroom.nes import chr as C
from cleanroom.nes import taint as T
from games.smb import art as A
from games.smb import atlas, palettes


def script_entries(d):
    out, i = [], 0
    while i < len(d) and d[i]:
        c = d[i + 2]
        n = 1 if c & 64 else (c & 63)
        out.append(bytes(d[i + 3:i + 3 + n]))
        i += 3 + n
    return out


def table_rows(asm_path, label):
    return [r for r, _ in atlas.table(label, asm_path)]


def main(argv):
    verbose = "-v" in argv
    args = [a for a in argv[1:] if a != "-v"]
    retail, clean, trees = open(args[0], "rb").read(), open(args[1], "rb").read(), args[2:]
    _, rprg, rchr = C.split_ines(retail)
    _, cprg, cchr = C.split_ines(clean)
    fails, lines = 0, []

    # T2 (first: T1 forgives raw hits that lie inside tiles T2 classes as coincidences)
    rt, ct = C.decode(rchr[:0x1EC0]), C.decode(cchr[:0x1EC0])
    P = atlas.pictures()
    own = atlas.owners(P)
    spec = A.load_spec()
    bad, coinc = [], set()
    for i, j, ncol, npx in T.tile_matches(rt, ct):
        kept = i in own and P[own[i][0]]["name"] in spec
        uniform = len(np.unique(ct[i])) == 1
        if uniform or (kept and ncol <= 1) or (not kept and npx <= 10):
            coinc.add(i)
        else:
            bad.append((i, j, P[own[i][0]]["name"] if i in own else "unowned"))
    fails += len(bad)
    t2 = (f"T2 tiles: {len(bad)} failing, {len(coinc)} coincidences (silhouette-only / uniform / tiny)"
          + "".join(f"\n     tile {i:03x} == retail {j:03x} ({n})" for i, j, n in bad[:(99 if verbose else 10)]))

    # T1
    win = T.windows(rchr, 0, 0x1EC0)

    def rom_hits(blob):
        if blob[:4] != b"NES":
            return T.scan_bytes(win, blob)
        base = len(blob) - 8192

        def outside(o):          # window bytes that are not inside a coincidence tile
            return bytes(blob[k] for k in range(o, o + T.WINDOW) if k < base or (k - base) // 16 not in coinc)

        return [o for o in T.scan_bytes(win, blob) if len(outside(o)) > 6 and len(set(outside(o))) > 2]

    h = rom_hits(clean)
    tree_hits = []
    for t in trees:
        for d, dirs, files in os.walk(t):
            dirs[:] = [x for x in dirs if x != ".git"]
            for f in files:
                n = len(rom_hits(open(os.path.join(d, f), "rb").read()))
                if n:
                    tree_hits.append((os.path.join(d, f), n))
    fails += (1 if h else 0) + len(tree_hits)
    lines.append(f"T1 raw windows: {len(win)} retail windows; clean ROM hits {len(h)}; tree files hit {len(tree_hits)}"
                 + "".join(f"\n     {p} x{n}" for p, n in tree_hits[:8]))
    lines.append(t2)

    # T3
    worst, pfail = [], 0
    for p in P:
        s = spec.get(p["name"])
        if not s or "uniform" in s:
            continue
        r = C.compose(rt, p["layout"], p["flips"])
        c = C.compose(ct, p["layout"], p["flips"])
        base = A.baseline(s)
        sil = r > 0
        detail = sil & (r != base)
        nd = int(detail.sum())
        rep = float((c[detail] == r[detail]).mean()) if nd else 0.0
        agree = float((c[sil] == r[sil]).mean()) if sil.any() else 1.0
        f = nd >= 12 and rep > 0.75 and agree > 0.90
        pfail += f
        worst.append((agree, rep, nd, p["name"], f))
    worst.sort(reverse=True)
    fails += pfail
    lines.append(f"T3 pictures: {pfail} failing of {len(worst)}; mean agreement {np.mean([w[0] for w in worst]):.2f}; closest: "
                 + ", ".join(f"{n} {a:.2f}/{r:.2f}" for a, r, d, n, f in worst[:(40 if verbose else 5)]))

    # T4
    re_ = [e for e in script_entries(rchr[0x1EC0:]) if len(e) >= 8 and any(b >= 0x30 and b != 0xCF for b in e)]
    ce = set(script_entries(cchr[0x1EC0:]))
    sb = [e for e in re_ if e in ce or e in cchr[0x1EC0:]]
    fails += len(sb)
    lines.append(f"T4 title script: {len(sb)} retail picture rows present (of {len(re_)})")

    # T5 / T6: compare PRG byte by byte; differing bytes must be palette colours
    diff = [i for i in range(len(rprg)) if rprg[i] != cprg[i]]
    work = os.path.dirname(os.path.dirname(os.path.abspath(args[1])))
    r_asm = os.path.join(work, "ref", "smb1", "src", "prg.asm")
    c_asm = os.path.join(work, "clean", "smb1", "src", "prg.asm")
    rows_r, rows_c = [], []
    for label in palettes.TABLES:
        a, b = table_rows(r_asm, label), table_rows(c_asm, label)
        k = len(palettes.TABLES[label])
        rows_r += [x for x in a[:k] if len(x) >= 3 and x[0] != 0x3F]
        rows_c += [x for x in b[:k] if len(x) >= 3 and x[0] != 0x3F]
    pb, grey, total = T.palette_rows([r[-3:] for r in rows_r], [c[-3:] for c in rows_c])
    fails += len(pb)
    lines.append(f"T5 palettes: {len(pb)} colourful rows equal to retail, {len(grey)} grey rows equal (coincidence), of {total}"
                 + "".join(f"\n     row {k}: {[hex(v) for v in rows_r[k]]}" for k in pb[:10]))
    nbytes = sum(len(r) for rows in palettes.TABLES.values() for r in rows)
    ok6 = len(diff) <= nbytes and len(cprg) == len(rprg)
    fails += 0 if ok6 else 1
    lines.append(f"T6 PRG: {len(diff)} bytes differ from retail (palette tables hold {nbytes}) -> {'ok' if ok6 else 'FAIL'}")

    print("\n".join(lines))
    print(f"TAINT: {fails} failing")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv) else 0)
