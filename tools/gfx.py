"""Small 4bpp tile helpers for graphics-text work (docs/re/graphics.md).

    python -X utf8 tools/gfx.py tags OUT.png      render every dialogue name tag (48x16) from the original ROM
"""
import sys
from PIL import Image
import romlib

TAG_BASE, TAG_STRIDE, TAG_SIZE = 0x251D34, 0x400, 0x180   # name tag n at TAG_BASE + (n+1)*0x400; "???" at 0x2522B4


TAG_NAMES = {1: 'Cou', 2: 'Ren', 3: 'Rowen', 4: 'Kea', 5: 'Cisqua', 6: 'Volks', 7: 'Chiruru', 8: 'Merchant',
             9: 'Enda', 10: 'Carlsen', 11: 'Arc Aile', 12: 'Masked Man', 13: 'Old Lady', 14: 'Old Man', 15: 'Priest'}
TAG_INK, TAG_SHADOW, TAG_BG = 1, 6, 4
TAG_TEXT = (2, 46, 3)          # text area columns [2, 46), glyph row 0 at tag row 3


def tag_font():
    from vwf import parse_art
    art = parse_art((romlib.ROOT / 'font' / 'tag.txt').read_text('utf-8'))
    return {ch: [[c == '#' for c in r] for r in rows] for ch, rows in art.items()}


def tag_width(font, s):
    return sum(2 if c == ' ' else len(font[c][0]) + 1 for c in s) - 1


def draw_tag(orig, name, font):
    """Original 0x180-byte tag -> same-size tag with `name` (palette indices kept)."""
    img = tiles_to_img(orig, 6, 2)
    px = [[img.getpixel((x, y))[0] // 17 for x in range(48)] for y in range(16)]
    lo, hi, y0 = TAG_TEXT
    for y in range(y0, 11):
        for x in range(lo, hi):
            px[y][x] = TAG_BG
    w = tag_width(font, name)
    assert w <= hi - lo, (name, w)
    x = lo + (hi - lo - w) // 2
    ink = set()
    for c in name:
        if c == ' ':
            x += 2
            continue
        g = font[c]
        for gy, row in enumerate(g):
            for gx, on in enumerate(row):
                if on:
                    ink.add((x + gx, y0 + gy))
        x += len(g[0]) + 1
    for (ix, iy) in ink:
        if (ix + 1, iy + 1) not in ink and iy + 1 < 16:
            px[iy + 1][ix + 1] = TAG_SHADOW
    for (ix, iy) in ink:
        px[iy][ix] = TAG_INK
    grey = [(i * 17, i * 17, i * 17) for i in range(16)]
    out = Image.new('RGB', (48, 16))
    for y in range(16):
        for x in range(48):
            out.putpixel((x, y), grey[px[y][x]])
    return img_to_tiles(out, grey)


def tag_patches(d):
    """[(offset, bytes)] replacing every dialogue name tag with its English name."""
    font = tag_font()
    out = []
    for n, name in TAG_NAMES.items():
        a = TAG_BASE + (n + 1) * TAG_STRIDE
        out.append((a, draw_tag(d[a:a + TAG_SIZE], name, font)))
    return out


LABEL_SIZE, READING_SIZE = 0x300, 0x180
COMBO_TABLE, COMBO_STRIDE, COMBO_N = 0x0C1830, 8, 201   # (label 96x16, reading 48x16) pointer pairs
COMBO_DESC = 0x0B99E0                                     # +0x14*i: combo record, description ptr at +0x10
ATTACK_TABLE, ATTACK_N = 0x5D6DA8, 56                     # enemy attack labels
ITEM_TABLE, ITEM_N = 0x0C1760, 10                         # item labels (+0x14*i, ptr at +0x10 of each 0x14 row)


def label_sets(d):
    """[(key, label offset, reading offset or None, context)] for every pre-rendered name label."""
    import struct
    u = lambda a: struct.unpack_from('<I', d, a)[0] - romlib.BASE
    out = []
    for i in range(COMBO_N):
        desc = u(COMBO_DESC + 0x14 * i + 0x10)
        ctx = romlib.decode(romlib.string_at(d, desc)) if romlib.string_at(d, desc) else ''
        out.append((f'C{i:03d}', u(COMBO_TABLE + COMBO_STRIDE * i), u(COMBO_TABLE + COMBO_STRIDE * i + 4), ctx))
    for i in range(ATTACK_N):
        out.append((f'A{i:03d}', u(ATTACK_TABLE + 4 * i), None, 'enemy attack'))
    for i in range(ITEM_N):
        out.append((f'I{i:03d}', u(ITEM_TABLE + 0x14 * i), None, 'item'))
    return out


LABEL_PAL = [(0, 0, 0), (90, 90, 120), (255, 255, 255)] + [(255, 0, 255)] * 13   # 1 = outline, 2 = fill


def label_img(d, a, w_sprites=3, pal=LABEL_PAL):
    """96x16 label: three 32x16 OBJ (4x2 tiles each)."""
    im = Image.new('RGB', (32 * w_sprites, 16))
    for s in range(w_sprites):
        im.paste(tiles_to_img(d[a + s * 256:a + s * 256 + 256], 4, 2, pal), (s * 32, 0))
    return im


READ_PAL = [(0, 0, 0)] + [(255, 255, 255)] * 15


def reading_img(d, a, pal=READ_PAL):
    """Reading line under a combo label: 96x8, 12 tiles in one row."""
    return tiles_to_img(d[a:a + READING_SIZE], 12, 1, pal)


def label_sheets(d, outdir, per=34):
    """Indexed sheets (label x3 + reading x3) for transcription, plus labels.tsv (key, context)."""
    from PIL import ImageDraw
    outdir.mkdir(parents=True, exist_ok=True)
    sets = label_sets(d)
    rows = []
    for k in range(0, len(sets), per):
        chunk = sets[k:k + per]
        sheet = Image.new('RGB', (630, 52 * len(chunk)), (40, 40, 60))
        dr = ImageDraw.Draw(sheet)
        for j, (key, a, r, ctx) in enumerate(chunk):
            dr.text((4, 52 * j + 18), key, fill=(255, 255, 0))
            sheet.paste(label_img(d, a).resize((288, 48), Image.NEAREST), (40, 52 * j + 2))
            if r is not None:
                sheet.paste(reading_img(d, r).resize((288, 24), Image.NEAREST), (334, 52 * j + 14))
        sheet.save(outdir / f'sheet_{k // per:02d}.png')
    (outdir / 'labels.tsv').write_text(''.join(f'{key}\t{ctx.replace(chr(10), " / ")}\n' for key, _, _, ctx in sets),
                                       'utf-8', newline='\n')
    return len(sets)


LABEL_W = 94     # usable px inside the 96x16 label (1 px outline each side)
LABELS_TSV = romlib.ROOT / 'font' / 'labels.tsv'   # key<TAB>JP<TAB>reading<TAB>English (translated label names)


def label_width(font, text):
    return font.text_width(text) + 1          # +1: right outline


def label_region(key):
    """(left x, usable px) of a label's text: item labels share their frame with the 'x05' count at x~86."""
    return (4, 78) if key.startswith('I') else (1, LABEL_W)


def outlined(font, text, w, h, lo, room, y0=1, tight=False, fill=2, edge=1, center=None):
    """Pixel grid (h rows of w) with text centred in [lo, lo+room) (or on x=center, clamped): fill colour +
    1 px outline. tight: letters share the outline pixel between them (advance - 1)."""
    tw = font.text_width(text) - (len(text) - 1 if tight else 0) + 1
    if tw > room:
        raise ValueError(f'{text!r} is {tw} px > {room}')
    ink = set()
    x = lo + (room - tw) // 2 if center is None else max(lo, min(lo + room - tw, center - tw // 2))
    for ch in text:
        for (gx, gy) in font.px[ord(ch)]:
            ink.add((x + gx, gy + y0))
        x += font.w[ord(ch)] - (1 if tight else 0)
    px = [[0] * w for _ in range(h)]
    for (ix, iy) in ink:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if 0 <= ix + dx < w and 0 <= iy + dy < h:
                    px[iy + dy][ix + dx] = edge
    for (ix, iy) in ink:
        px[iy][ix] = fill
    return px


def pack_obj(px, sprite_w, sprite_h):
    """Pixel grid -> 4bpp bytes for consecutive OBJ sprites laid left to right (1D mapping, row-major tiles)."""
    out = bytearray()
    for s in range(len(px[0]) // sprite_w):
        for t in range((sprite_w // 8) * (sprite_h // 8)):
            ty, tx = (t // (sprite_w // 8)) * 8, s * sprite_w + (t % (sprite_w // 8)) * 8
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(px[ty + y][tx + x] | px[ty + y][tx + x + 1] << 4)
    return bytes(out)


def draw_label(font, text, key='C'):
    """English label -> 0x300 bytes: three 32x16 OBJ, fill = index 2, 1 px outline = index 1, centered."""
    lo, room = label_region(key)
    try:
        px = outlined(font, text, 96, 16, lo, room)
    except ValueError as e:
        raise ValueError(f'label {key}: {e}')
    return pack_obj(px, 32, 16)


TABS_AT = 0x08DBDC                 # menu character tabs: 5 OBJ 32x16 (0x100 each), fill 2 / outline 1
TAB_NAMES = ['Cou', 'Ren', 'Cisqua', 'Rowen', 'Kea']


def tab_patches():
    import vwf
    font = vwf.Font()
    # the sprite sits ~6 px right of the tab frame's centre: centre the name on x=11 like the Japanese
    return [(TABS_AT + 0x100 * i, pack_obj(outlined(font, n, 32, 16, 0, 32, y0=2, tight=True, center=11), 32, 16))
            for i, n in enumerate(TAB_NAMES)]


def read_labels():
    rows = {}
    if LABELS_TSV.exists():
        for line in LABELS_TSV.read_text('utf-8').splitlines():
            if line and not line.startswith('#'):
                k, jp, reading, en = line.split('\t')
                rows[k] = en
    return rows


def label_patches(d):
    """[(offset, bytes)]: every translated name label redrawn in place; combo reading lines blanked."""
    import vwf
    font, en = vwf.Font(), read_labels()
    out = []
    for key, a, r, _ in label_sets(d):
        if key in en:
            out.append((a, draw_label(font, en[key], key)))
            if r is not None:
                out.append((r, bytes(READING_SIZE)))
    return out


POOL_AT, POOL_N = 0x19C83C, 116    # 8x8 UI tile pool; the game assembles header sprites in VRAM from these tiles
SPEED = [[13, 29, 37], [14, 30, 38], [15, 31, 39], [17, 33, 41], [18, 34, 42], [19, 35, 43]]  # 3 identical copies
# (name, 4x4 layout of pool tiles (lists = identical copies, None = blank), [(text, x, y)]) - layouts from VRAM dumps
COMPOSITES = [
    ('item info header', [[20], [21], None, None, [24], [25], [26], None,
                          None, SPEED[0], SPEED[1], SPEED[2], None, SPEED[3], SPEED[4], SPEED[5]],
     [('Heal', 1, 8), ('Speed', 10, 18)]),
    ('combo info header', [[4], [5], [6], None, [8], [9], [10], None,
                           None, SPEED[0], SPEED[1], SPEED[2], None, SPEED[3], SPEED[4], SPEED[5]],
     [('Attack', 0, 8), ('Speed', 10, 18)]),
]
TEXT_FILL, TEXT_SHADOW = 2, 3


def tag_text(px, font, text, x, y, fill, shadow):
    """Draw tag-font text into a pixel grid with a shadow right/below."""
    ink = set()
    for c in text:
        if c == ' ':
            x += 2
            continue
        for gy, row in enumerate(font[c]):
            for gx, on in enumerate(row):
                if on:
                    ink.add((x + gx, y + gy))
        x += len(font[c][0]) + 1
    for (ix, iy) in ink:
        for (sx, sy) in ((ix + 1, iy), (ix, iy + 1), (ix + 1, iy + 1)):
            if (sx, sy) not in ink and 0 <= sy < len(px) and 0 <= sx < len(px[0]):
                px[sy][sx] = shadow
    for (ix, iy) in ink:
        px[iy][ix] = fill


def composite_patches(d):
    """[(offset, 32 bytes)] for pool tiles, from English redraws of each composite header sprite."""
    font = tag_font()
    out = {}
    for name, layout, words in COMPOSITES:
        px = [[0] * 32 for _ in range(32)]
        for k, src in enumerate(layout):
            if src:
                img = tiles_to_img(d[POOL_AT + 32 * src[0]:POOL_AT + 32 * src[0] + 32], 1, 1)
                for y in range(8):
                    for x in range(8):
                        px[(k // 4) * 8 + y][(k % 4) * 8 + x] = img.getpixel((x, y))[0] // 17
        px = [[0 if v in (TEXT_FILL, TEXT_SHADOW) else v for v in row] for row in px]
        for text, x, y in words:
            tag_text(px, font, text, x, y, TEXT_FILL, TEXT_SHADOW)
        for k, src in enumerate(layout):
            tile = pack_obj([row[(k % 4) * 8:(k % 4) * 8 + 8] for row in px[(k // 4) * 8:(k // 4) * 8 + 8]], 8, 8)
            if src is None:
                if any(tile):
                    raise ValueError(f'{name}: tile {k} needs ink but the game draws it blank')
                continue
            for p in src:
                a = POOL_AT + 32 * p
                if a in out and out[a] != tile:
                    raise ValueError(f'{name}: pool tile {p} shared with a different drawing')
                out[a] = tile
    return sorted(out.items())


BADGES = [(0x19C23C, 'All'), (0x19C33C, 'Single')]   # 全体 / 単体: 32x16 OBJ, gradient badge, text fill E + outline 1


STATUS_LABELS = [(0x19C43C, 'React'), (0x19C53C, 'Ailment'), (0x19C63C, 'Downed'), (0x19C73C, 'Fallen')]
# リアクト / 状態異常 / 行動不能 / 戦闘不能: 32x16 OBJ, text fill 2 + shadow (1 or 3), rows 5-13


def status_patches(d):
    font = tag_font()
    out = []
    for a, text in STATUS_LABELS:
        img = tiles_to_img(d[a:a + 256], 4, 2)
        vals = {img.getpixel((x, y))[0] // 17 for x in range(32) for y in range(16)} - {0, TEXT_FILL}
        assert len(vals) == 1, (hex(a), vals)
        px = [[0] * 32 for _ in range(16)]
        tw = tag_width(font, text) + 1
        tag_text(px, font, text, (32 - tw) // 2, 6, TEXT_FILL, vals.pop())
        out.append((a, pack_obj(px, 32, 16)))
    return out


PLATES_AT = 0x0C45F8   # battle HP-bar name plates: 27 tiles in one 8-px row; (first tile, tiles, name)
PLATES = [(0, 4, 'Cou'), (10, 4, 'Ren'), (14, 4, 'Cisqua'), (18, 5, 'Rowen'), (23, 4, 'Kea')]


def plate_patches(d):
    """Text 2 on interior F; redrawn only on interior pixels so the slanted borders stay."""
    font = tag_font()
    img = tiles_to_img(d[PLATES_AT:PLATES_AT + 27 * 32], 27, 1)
    px = [[img.getpixel((x, y))[0] // 17 for x in range(27 * 8)] for y in range(8)]
    for t0, n, name in PLATES:
        x0 = t0 * 8
        for y in range(8):
            for x in range(x0, x0 + n * 8):
                if px[y][x] == 2:
                    px[y][x] = 0xF
        interior = {(x, y) for y in range(8) for x in range(x0, x0 + n * 8) if px[y][x] == 0xF}
        x = x0 + 1
        for c in name:
            g = font[c]
            for gy, row in enumerate(g):
                for gx, on in enumerate(row):
                    if on and gy < 7:   # descenders may cross row 7 (bottom border): drop those pixels
                        assert (x + gx, gy) in interior, f'plate {name}: ink outside the plate at {x + gx},{gy}'
                        px[gy][x + gx] = 2
            x += len(g[0]) + 1
    return [(PLATES_AT, pack_obj(px, 27 * 8, 8))]


def badge_patches(d):
    import collections, vwf
    font = vwf.Font()
    out = []
    for a, text in BADGES:
        img = tiles_to_img(d[a:a + 256], 4, 2)
        px = [[img.getpixel((x, y))[0] // 17 for x in range(32)] for y in range(16)]
        for y, row in enumerate(px):
            bg = collections.Counter(v for v in row if v not in (0, 1, 0xE)).most_common(1)
            nz = [x for x, v in enumerate(row) if v]
            if bg and nz:
                for x in range(nz[0], nz[-1] + 1):
                    if row[x] in (1, 0xE):
                        row[x] = bg[0][0]
        txt = outlined(font, text, 32, 16, 2, 28, y0=2, tight=True, fill=0xE, edge=1)
        for y in range(16):
            for x in range(32):
                if txt[y][x]:
                    px[y][x] = txt[y][x]
        out.append((a, pack_obj(px, 32, 16)))
    return out


def tiles_to_img(data, w_tiles, h_tiles, pal=None):
    """Row-major 4bpp tiles -> PIL image (palette: list of 16 RGB tuples, default grey ramp)."""
    pal = pal or [(i * 17, i * 17, i * 17) for i in range(16)]
    img = Image.new('RGB', (w_tiles * 8, h_tiles * 8))
    for t in range(w_tiles * h_tiles):
        tile = data[t * 32:t * 32 + 32]
        for y in range(8):
            for x in range(8):
                v = (tile[y * 4 + x // 2] >> (4 * (x & 1))) & 15
                img.putpixel(((t % w_tiles) * 8 + x, (t // w_tiles) * 8 + y), pal[v])
    return img


def img_to_tiles(img, pal):
    """Inverse of tiles_to_img; every pixel colour must be in pal."""
    w_tiles, h_tiles = img.width // 8, img.height // 8
    out = bytearray()
    for t in range(w_tiles * h_tiles):
        for y in range(8):
            for x in range(0, 8, 2):
                px = [pal.index(img.getpixel(((t % w_tiles) * 8 + x + i, (t // w_tiles) * 8 + y))[:3]) for i in (0, 1)]
                out.append(px[0] | px[1] << 4)
    return bytes(out)


def bgr555(data):
    return [((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31)
            for v in (int.from_bytes(data[i:i + 2], 'little') for i in range(0, len(data), 2))]


if __name__ == '__main__':
    d = romlib.load()
    if sys.argv[1] == 'label-check':
        # python -X utf8 tools/gfx.py label-check FILE.tsv : every English label fits 94 px and uses known glyphs
        import vwf
        font, bad = vwf.Font(), 0
        keys = {k for k, *_ in label_sets(d)}
        seen = set()
        for i, line in enumerate(open(sys.argv[2], encoding='utf-8-sig').read().splitlines()):
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) != 4 or parts[0] not in keys or parts[0] in seen:
                print(f'line {i + 1}: need key<TAB>JP<TAB>reading<TAB>English with a known, unique key'); bad += 1
                continue
            seen.add(parts[0])
            en = parts[3]
            miss = [c for c in en if not (0x20 <= ord(c) < 0x7F)]
            if miss or not en:
                print(f'{parts[0]}: empty or non-ASCII {miss}'); bad += 1
            elif label_width(font, en) > label_region(parts[0])[1]:
                print(f'{parts[0]}: "{en}" is {label_width(font, en)} px > {label_region(parts[0])[1]}'); bad += 1
        missing = sorted(keys - seen)
        if missing:
            print(f'missing keys: {missing[:20]}{" ..." if len(missing) > 20 else ""}'); bad += 1
        print('OK' if not bad else f'{bad} errors')
        sys.exit(1 if bad else 0)
    elif sys.argv[1] == 'label-preview':
        pal = LABEL_PAL
        pats = label_patches(d)
        labels = [b for a, b in pats if len(b) == LABEL_SIZE]
        sheet = Image.new('RGB', (100 * 4, 18 * ((len(labels) + 3) // 4)), (40, 40, 60))
        for k, b in enumerate(labels):
            im = Image.new('RGB', (96, 16))
            for s in range(3):
                im.paste(tiles_to_img(b[s * 256:s * 256 + 256], 4, 2, pal), (s * 32, 0))
            sheet.paste(im, ((k % 4) * 100, (k // 4) * 18))
        sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(sys.argv[2])
    elif sys.argv[1] == 'label-sheets':
        print(label_sheets(d, romlib.ROOT / 'work' / 'labels'), 'labels')
    elif sys.argv[1] == 'labels':
        # 96x16 labels = 3 OBJ 32x16 (4x2 tiles each), 0x300 bytes; tables at 0x5D6DA8 (56 ptrs) and 0x0C1760
        import struct
        addrs = [struct.unpack_from('<I', d, 0x5D6DA8 + 4 * i)[0] - romlib.BASE for i in range(56)]
        addrs += [struct.unpack_from('<I', d, 0x0C1760 + 0x14 * i)[0] - romlib.BASE for i in range(10)]
        sheet = Image.new('RGB', (100 * 4, 18 * ((len(addrs) + 3) // 4)))
        for k, a in enumerate(addrs):
            im = Image.new('RGB', (96, 16))
            for s in range(3):
                im.paste(tiles_to_img(d[a + s * 256:a + s * 256 + 256], 4, 2), (s * 32, 0))
            sheet.paste(im, ((k % 4) * 100, (k // 4) * 18))
        sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(sys.argv[2])
    elif sys.argv[1] == 'tags-en':
        pal = [(0, 0, 0), (255, 255, 255), (255, 213, 57), (255, 49, 49), (189, 0, 16), (148, 0, 8), (115, 0, 0),
               (82, 0, 0), (49, 0, 0)] + [(0, 255, 0)] * 7
        sheet = Image.new('RGB', (51 * 4, 18 * 4))
        for k, (a, b) in enumerate(tag_patches(d)):
            sheet.paste(tiles_to_img(b, 6, 2, pal), ((k % 4) * 51, (k // 4) * 18))
        sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(sys.argv[2])
    elif sys.argv[1] == 'tags':
        n = 40
        sheet = Image.new('RGB', (48 * 4 + 12, 18 * ((n + 4) // 4)))
        for i in range(-1, n - 1):
            a = TAG_BASE + (i + 1) * TAG_STRIDE if i >= 0 else 0x2522B4
            img = tiles_to_img(d[a:a + TAG_SIZE], 6, 2)
            k = i + 1
            sheet.paste(img, ((k % 4) * 51, (k // 4) * 18))
        sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(sys.argv[2])
