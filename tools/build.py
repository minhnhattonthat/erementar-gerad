"""Build the English ROM: build/eg_en.gba.

    python -X utf8 tools/build.py [--marker] [--qa ID=TEXT ...] [--out PATH]

Strings with an `en` (or a --qa override, or every string with --marker) are written to free space as pair cells
(tools/vwf.py) and every pointer slot of that string is repointed. Untranslated strings are left untouched.
The pair glyphs actually used are rendered into ROM and asm/pairs.asm is assembled on top (armips).
"""
import argparse, json, struct, subprocess, sys
from pathlib import Path
import fit, gfx, romlib, vwf

FREE_LO, FREE_HI = 0x640000, 0x800000
OUT = romlib.ROOT / 'build' / 'eg_en.gba'
MARKER = 'The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.'


class Free:
    def __init__(self, d, lo, hi):
        assert all(b == 0xFF for b in d[lo:hi]), 'free space not 0xFF'
        self.d, self.pos, self.hi = d, lo, hi

    def put(self, data, align=4):
        self.pos = (self.pos + align - 1) & ~(align - 1)
        a = self.pos
        if a + len(data) > self.hi:
            raise SystemExit(f'free space overflow at {a:06X} (+{len(data)})')
        self.d[a:a + len(data)] = data
        self.pos += len(data)
        return a


def load_entries():
    return [e for p in sorted(romlib.SCRIPT_DIR.glob('*.json')) for e in json.loads(p.read_text('utf-8'))]


def marker_text(e):
    lines = e['jp'].split('\n')
    return '\n'.join((e['id'] + ' ' if i == 0 else '') + MARKER[:2 * len(l)] for i, l in enumerate(lines))


def encode(s):
    """Text -> list of cells (the string bytes are their join + a NUL terminator). Non-ASCII = Shift-JIS cell."""
    bad = [c for c in s if c != '\n' and (ord(c) < 0x20 or 0x7F <= ord(c) < 0x80
                                          or (ord(c) >= 0x80 and len(c.encode('cp932', 'replace')) != 2))]
    if bad:
        raise ValueError(f'unencodable {bad!r} in {s!r}')
    return vwf.to_cells(s)


def assemble(rom_path, syms):
    exe = romlib.ROOT / 'tools' / 'armips' / 'armips.exe'
    cmd = [str(exe), str(romlib.ROOT / 'asm' / 'pairs.asm'), '-strequ', 'BUILD_ROM', str(Path(rom_path).resolve())]
    for k, v in syms.items():
        cmd += ['-equ', k, hex(v)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit('armips failed:\n' + r.stdout + r.stderr)


def build(out, marker=False, qa=None, identity=False):
    """identity: every string relocated with en = jp (the test that slots and relocation are exact)."""
    qa = qa or {}
    d = bytearray(romlib.load())
    font = vwf.Font()
    texts, errors = {}, []
    for e in load_entries():
        en = qa.get(e['id']) or (marker_text(e) if marker else e['jp'] if identity else e.get('en'))
        if en is None:
            continue
        if not (marker or identity):
            lines, err = fit.layout(e, en)
            if err:
                errors.append(f"{e['id']}: {err}")
            en = '\n'.join(lines)
        texts[e['id']] = (en, e['slots'])
    if errors:
        raise SystemExit(f'{len(errors)} strings do not fit:\n' + '\n'.join(errors[:30]))
    enc = {i: encode(t) for i, (t, _) in texts.items()}

    free = Free(d, FREE_LO, FREE_HI)
    code_at = free.put(b'\0' * 0x400)            # asm/pairs.asm code + literal pools
    widths = free.put(font.width_table())
    pairs = sorted({c for cs in enc.values() for c in cs if c[0] < 0x80 and c != b'nn'})
    missing = sorted({chr(x) for c in pairs for x in c if x and x not in font.px})
    if missing:
        raise SystemExit(f'font lacks {missing}')
    tab = [0] * (96 * 128)
    glyphs = [font.pair_tiles(ord('?'), 0)]
    for c in pairs:
        tab[(c[0] - 0x20) * 128 + c[1]] = len(glyphs)
        glyphs.append(font.pair_tiles(c[0], c[1]))
    pair_tab = free.put(struct.pack('<%dH' % len(tab), *tab))
    pair_gfx = free.put(b''.join(glyphs))
    for i, cs in enc.items():
        a = free.put(b''.join(cs) + b'\0')
        for s in texts[i][1]:
            struct.pack_into('<I', d, int(s, 16), romlib.BASE + a)
    if not identity:
        # name tags, skill/attack/item labels (font/labels.tsv): redrawn in place, same size
        for a, b in gfx.tag_patches(d) + gfx.label_patches(d) + gfx.tab_patches() + gfx.composite_patches(d) + gfx.badge_patches(d) + gfx.status_patches(d):
            d[a:a + len(b)] = b
    Path(out).parent.mkdir(exist_ok=True)
    Path(out).write_bytes(d)
    # every text pointer slot and where it now points, for jp_left.py --slots (leftover-Japanese gate)
    with open(Path(out).with_suffix('.slots.txt'), 'w', newline='\n') as f:
        for e in load_entries():
            for s in e['slots']:
                f.write('%s %06X\n' % (s, struct.unpack_from('<I', d, int(s, 16))[0] - romlib.BASE))
    # Japanese we keep on purpose (debug labels): jp_left.py --known
    with open(Path(out).with_suffix('.known.txt'), 'w', newline='\n') as f:
        f.writelines(e['id'] + '\n' for e in load_entries() if fit.form(e) == 'keep')
    assemble(out, {'CODE_AT': romlib.BASE + code_at, 'WIDTHS': romlib.BASE + widths,
                   'PAIR_TAB': romlib.BASE + pair_tab, 'PAIR_GFX': romlib.BASE + pair_gfx})
    print(f'{len(enc)} strings, {len(pairs)} pair glyphs, free space used to {free.pos:06X}; wrote {out}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--marker', action='store_true')
    ap.add_argument('--qa', action='append', default=[], help='ID=TEXT override (\\n = newline)')
    ap.add_argument('--identity', action='store_true', help='relocate every string with en = jp')
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()
    build(a.out, a.marker, {k: v.replace('\\n', '\n') for k, v in (q.split('=', 1) for q in a.qa)}, a.identity)
