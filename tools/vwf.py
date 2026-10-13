"""English font for the pair-glyph renderer (docs/re/font.md).

A text cell is two ASCII bytes drawn as one 16x16 OBJ glyph; the game advances by width(a) + width(b).
Font art (font/en11.txt, from the monster-guardians project): 'char X' + rows of '#'/'.'; glyphs are trimmed to
their inked columns, advance = inked width + 1 px gap; space = SPACE px.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / 'font' / 'en11.txt'
SPACE = 3
ROWS = 13         # art rows; row 0 lands on glyph-cell row 0 (Japanese glyphs use rows 0-11)
CELL = 16         # pair glyph is one 16x16 sprite
ALT_N = 0x7F      # second 'n' of an "nn" cell: 6E 6E is the newline code
SJIS_W = 12       # advance of a Japanese (SJIS) cell


def parse_art(text):
    glyphs, cur = {}, None
    for line in text.splitlines():
        if line.startswith('char '):
            name = line[5:]
            cur = ' ' if name == 'space' else name
            glyphs[cur] = []
        elif line and set(line) <= {'.', '#'} and cur is not None:
            glyphs[cur].append(line)
    return glyphs


class Font:
    def __init__(self):
        self.px, self.w = {}, {}
        for ch, rows in parse_art(ART.read_text(encoding='utf-8')).items():
            assert len(rows) == ROWS, ch
            cols = [x for x in range(len(rows[0])) if any(r[x] == '#' for r in rows)]
            if ch == ' ' or not cols:
                self.px[ord(ch)], self.w[ord(ch)] = [], SPACE
                continue
            lo, hi = cols[0], cols[-1]
            self.px[ord(ch)] = [(x - lo, y) for y, r in enumerate(rows) for x in range(lo, hi + 1) if r[x] == '#']
            self.w[ord(ch)] = hi - lo + 2
        self.px[ALT_N], self.w[ALT_N] = self.px[ord('n')], self.w[ord('n')]
        self.px[0], self.w[0] = [], 0   # odd-length tail: "x\0"

    def width_table(self):
        """128 bytes: advance per byte value (0 for unused)."""
        return bytes(self.w.get(i, 0) for i in range(128))

    def text_width(self, s):
        return sum(self.w[ord(c)] for c in s)

    def missing(self, s):
        return sorted({c for c in s if ord(c) not in self.px})

    def pair_tiles(self, a, b):
        """4bpp 16x16 glyph for bytes a, b: tiles TL, TR, BL, BR (32 bytes each), ink = palette index 1."""
        img = [[0] * CELL for _ in range(CELL)]
        for (x, y) in self.px[a]:
            img[y][x] = 1
        for (x, y) in self.px[b]:
            if self.w[a] + x < CELL:
                img[y][self.w[a] + x] = 1
        out = bytearray()
        for ty, tx in ((0, 0), (0, 8), (8, 0), (8, 8)):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(img[ty + y][tx + x] | img[ty + y][tx + x + 1] << 4)
        return bytes(out)


def to_cells(s):
    """Text -> list of 2-byte cells. ASCII letters pair up; any other character is its own Shift-JIS cell (the
    game's font). '\\n' = the 'nn' newline cell. A lone ASCII letter before a SJIS cell or line end gets a space,
    at the very end a 0."""
    out, pend = [], b''

    def flush(last):
        nonlocal pend
        if pend:
            out.append(pend + (b'\0' if last else b' '))
            pend = b''

    for ch in s:
        if ch == '\n':
            flush(False)
            out.append(b'nn')
        elif ord(ch) < 0x80:
            pend += ch.encode('ascii')
            if len(pend) == 2:
                out.append(bytes([0x6E, ALT_N]) if pend == b'nn' else pend)
                pend = b''
        else:
            flush(False)
            out.append(ch.encode('cp932'))
    flush(True)
    return out


def cell_width(font, c):
    return SJIS_W if c[0] >= 0x80 else font.w[c[0]] + font.w[c[1]]
