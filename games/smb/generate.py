"""CLEAN ROOM: spec + our art -> CHR, palettes -> assembled ROM.

    python -m games.smb.generate [work dir = D:/n64work/smb]

Reads only games/smb (spec, art, code) and the pristine disassembly (code,
levels, music: kept). Never reads the retail ROM.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np

from cleanroom.nes import chr as C
from games.smb import art as A
from games.smb import atlas, font, palettes, title

HERE = os.path.dirname(os.path.abspath(__file__))


def build_pictures():
    """-> (pictures, {name: index image})"""
    spec, art = A.load_spec(), A.load_art()
    P = atlas.pictures()
    known = {p["name"] for p in P}
    stray = sorted(set(art) - known)
    if stray:
        print("art blocks without a picture:", " ".join(stray))
    return P, {p["name"]: A.render(p, spec, art) for p in P if p["kind"] not in ("glyph",)}


def build_chr():
    meta = json.load(open(os.path.join(HERE, "spec", "meta.json")))
    P, imgs = build_pictures()
    tiles = np.zeros((512, 8, 8), np.uint8)
    own = atlas.owners(P)
    for t, (i, r, c) in own.items():
        p = P[i]
        if p["kind"] == "glyph":
            continue
        px = imgs[p["name"]][r * 8:r * 8 + 8, c * 8:c * 8 + 8]
        f = p["flips"][r][c]
        if f & 1:
            px = px[:, ::-1]
        tiles[t] = px
    for t, ch in atlas.FONT.items():
        tiles[t] = font.glyph(ch) * meta["font_index"]
    for t, px in title.tiles().items():
        tiles[0x100 + t] = px
    data = bytearray(C.encode(tiles))
    data[0x1EC0:0x2000] = title.script()
    return bytes(data), tiles


def patch_palettes(asm: str) -> str:
    lines = asm.split("\n")
    for label, rows in palettes.TABLES.items():
        i = next(k for k, l in enumerate(lines) if l.startswith(label + ":")) + 1
        for row in rows:
            while not lines[i].strip().startswith(".db"):
                i += 1
            m = re.match(r"(\s*\.db\s+)([^;]*?)(\s*;.*)?$", lines[i])
            n = len([v for v in m.group(2).split(",") if v.strip()])
            assert n == len(row), f"{label}: row has {n} bytes, ours {len(row)}"
            body = ", ".join(f"${v:02x}" for v in row)
            lines[i] = m.group(1) + body + (m.group(3) or "")
            i += 1
    return "\n".join(lines)


def main(argv):
    work = argv[1] if len(argv) > 1 else "D:/n64work/smb"
    src, dst = os.path.join(work, "ref", "smb1"), os.path.join(work, "clean", "smb1")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git", "bin", "*.chr", "*.nes"))
    os.makedirs(os.path.join(dst, "bin"))
    p = os.path.join(dst, "src", "prg.asm")
    asm = open(p, encoding="latin-1", newline="").read()
    open(p, "w", encoding="latin-1", newline="").write(patch_palettes(asm))
    data, tiles = build_chr()
    open(os.path.join(dst, "smb1.chr"), "wb").write(data)
    r = subprocess.run([os.path.join(work, "tools", "asm6f.exe"), "smb1.asm", "-q", "bin/smb1.nes"], cwd=dst,
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("asm6f failed:\n" + (r.stdout + r.stderr)[-1500:])
    rom = open(os.path.join(dst, "bin", "smb1.nes"), "rb").read()
    out = os.path.join(work, "clean", "smb.nes")
    open(out, "wb").write(rom)
    art = A.load_art()
    drawn = sum(1 for n in A.load_spec() if n in art)
    print(f"clean ROM {out}: {len(rom)} bytes sha1 {hashlib.sha1(rom).hexdigest()[:12]}; "
          f"{drawn}/{len(A.load_spec())} pictures hand-drawn, {len(atlas.FONT)} glyphs, {len(title.SLOTS)} title tiles, "
          f"{len(palettes.TABLES)} palette tables")


if __name__ == "__main__":
    main(sys.argv)
