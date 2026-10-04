"""Background pictures that are easier to state as rules than as ASCII.

Each function returns art rows in the same alphabet as art/*.txt
(`.` / `?` = take the baseline, `1 2 3` = colour index, `!` lines =
directives). art.load_art() merges these under the hand-drawn files.
Roles: 1 = light, 2 = mid / dark, 3 = black line (per background palette).
"""


def _cols(profile, rows):
    return [profile for _ in range(rows)]


# pipe cross-section, light from the left; cols 16-23 are the shared uniform fill tile (colour 2)
_LIP = "3" + "1111" + "2" + "11111111" + "2" + "1" + "2" * 15 + "3"
_SHAFT = ".." + "3" + "11" + "2" + "11111111" + "2" + "1" + "2" * 13 + "3" + ".."


def pipe_up():
    lip = []
    for y in range(12):                         # dithered edge between the lit and the shaded side
        d = ("1" if y % 2 == 0 else "2") + ("1" if y % 4 == 0 else "2")
        lip.append(_LIP[:16] + d + _LIP[18:])
    return ["3" * 32, "3" + "1" * 15 + "2" * 15 + "3"] + lip + ["3" * 32, ".." + "3" * 28 + ".."] + _cols(_SHAFT, 8)


def pipe_side():
    """mouth on the left (16 px lip), shaft to the right, light from above"""
    prof = "3" + "1111" + "2" + "11111111" + "2" + "1" + "2" * 15 + "3"          # top -> bottom
    rows = []
    for y in range(32):
        c = prof[y]
        lip = "3" + ("1" + c * 12 if 0 < y < 31 else "3" * 13) + "33"
        if y in (0, 31):
            shaft = "." * 10 + "3" * 6
        elif y in (1, 30):
            shaft = "3" * 16
        else:
            shaft = c * 10 + "3" + ("11" if y % 2 else "12") + "211"
        rows.append(lip + shaft)
    return rows


def cloud_bush():
    top = ["........" + r + "........" for r in (
        "......1111......", ".....111111.....", "...111111111....", "..1111111111.1..",
        "..1111111111111.", "..11111111211111", ".111111111121111", "1111111111111111")]
    mid = ["1" * 32, "1" * 32, "1" * 27 + "21111", "1" * 26 + "211111", "11121" + "1" * 21 + "221111", "1121" + "1" * 28,
           "1221" + "1" * 28, "1" * 32]
    bot = ["..1111111111111111111111111111..", "...1111111111111111111111111111.", "....1111211111111111112111111111",
           "....112211111122111111122111111.", ".....22111111221111111112211111.", "........122222111122222111111...",
           ".........222222.22222222.22.....", "...........222....2222.........."]
    return ["!outline 3"] + top + mid + bot


def hill():
    rows = ["2" * 32] * 16
    spots = {9: "..3.....", 10: "..33....", 11: "..33..3.", 12: "..3...33", 13: "......33", 14: "......3."}
    out = []
    for y, r in enumerate(rows):
        if y in spots:
            r = r[:8] + spots[y].replace(".", "2") + r[16:]
        if y in (3, 4, 5):                       # one more dab near the summit
            r = r[:17] + "3" + r[18:]
        out.append(r)
    return ["!edge 1 lrt"] + out


def tree():
    crown = []
    for y in range(24):
        n = max(0, min(16, y - 4 + (y - 8) // 2))          # shade grows toward the bottom right
        crown.append("1" * (16 - n) + "2" * n)
    trunk = ["....12212222...." if y % 2 else ".....1221222...." for y in range(8)]
    for y, x in ((4, 8), (5, 5), (6, 10), (7, 3), (7, 7)):          # leaf specks
        crown[y] = crown[y][:x] + "2" + crown[y][x + 1:]
    return ["!outline 3"] + crown + trunk


def tree_ledge():
    top = ["1" * 32] * 4 + ["11121112" * 4] + ["1" * 32] * 3 + ["1112" * 8, "12" * 16] + ["2" * 32] * 6
    trunk = ["........" + "21222122" * 2 + "........"] * 8
    return ["!outline 3 nobottom"] + top + trunk


def brick():
    t45 = ["11111111", "22223222", "22223222", "33333333", "32222222", "32222222", "32222222", "33333333"]
    t47 = ["22223222", "22223222", "22223222", "33333333", "32222222", "32222222", "32222222", "33333333"]
    return [r + r for r in t45] + [r + r for r in t47]


def castle_parts():
    b = brick()
    row0 = ["1111....", "2223....", "2223....", "3333....", "3222....", "3222....", "3222....", "33333333"]
    row0b = ["...11111", "...22322", "...22322", "...33333", "...32222", "...32222", "...32222", "33333333"]
    arch_l = ["22233333", "22333333", "23333333", "23333333", "33333333", "33333333", "33333333", "33333333"]
    top = [row0[y] + row0b[y] + b[y][:8] + b[8 + y][:8] for y in range(8)]
    bot = [arch_l[y] + arch_l[y][::-1] + "????????" * 2 for y in range(8)]
    return top + bot


def ground():
    rows = ["2111111111111112", "1122222222222223"] + ["1222222222222223"] * 12 + ["1222222222222233", "2333333333333332"]
    rows = [list(r) for r in rows]
    for y, x, c in ((4, 5, "3"), (4, 6, "3"), (5, 5, "1"), (9, 10, "3"), (10, 10, "3"), (10, 11, "1"), (11, 4, "3"), (6, 12, "1")):
        rows[y][x] = c                              # pebbles
    return ["".join(r) for r in rows]


def stair_block():
    out = []
    for y in range(16):
        r = ""
        for x in range(16):
            if 3 <= x <= 12 and 3 <= y <= 12:
                r += "2"
            elif x + y < 15 and (x < 3 or y < 3):
                r += "1"
            else:
                r += "3"
        out.append(r)
    return out


def qblock():
    q = ["..22222...", ".2211122..", ".22...22..", "......22..", ".....222..", "....222...", "....22....", "..........",
         "....22....", "....22...."]
    rows = [".11111111111111."] + ["1111111111111113"] * 14 + ["3333333333333333"]
    out = []
    for y, r in enumerate(rows):
        if 3 <= y <= 12:
            g = q[y - 3].replace("1", "2")              # black mark with a brown drop shadow
            sh = "." + (q[y - 4].replace("1", "2") if y > 3 else "." * 10)[:9]
            r = r[:3] + "".join("3" if c == "2" else "2" if s == "2" else k for c, s, k in zip(g, sh, r[3:13])) + r[13:]
        if y in (2, 13):
            r = r[:2] + "3" + r[3:13] + "3" + r[14:]
        out.append(r)
    return out


def used_block():
    rows = [".22222222222222."] + ["2222222222222223"] * 14 + [".33333333333333."]
    return [r[:3] + "3" + r[4:12] + "3" + r[13:] if y in (3, 12) else r for y, r in enumerate(rows)]


def fence():
    post, rail_hi, rail, rail_lo = "....12222223....", "1111122222231111", "2222122222232222", "3333122222233333"
    half = [post, post, rail_hi, rail, rail_lo, post, post, post]
    return half + half


CODE = {f.__name__: f for f in (pipe_up, pipe_side, cloud_bush, hill, tree, tree_ledge, brick, castle_parts, ground,
                                stair_block, qblock, used_block, fence)}
