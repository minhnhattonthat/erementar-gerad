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


def draw_label(font, text, key='C'):
    """English label -> 0x300 bytes: three 32x16 OBJ, fill = index 2, 1 px outline = index 1, centered."""
    lo, room = label_region(key)
    w = label_width(font, text)
    if w > room:
        raise ValueError(f'label {key} {text!r} is {w} px > {room}')
    ink = set()
    x = lo + (room - w) // 2
    for ch in text:
        for (gx, gy) in font.px[ord(ch)]:
            ink.add((x + gx, gy + 1))
        x += font.w[ord(ch)]
    px = [[0] * 96 for _ in range(16)]
    for (ix, iy) in ink:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if 0 <= ix + dx < 96 and 0 <= iy + dy < 16:
                    px[iy + dy][ix + dx] = 1
    for (ix, iy) in ink:
        px[iy][ix] = 2
    out = bytearray()
    for s in range(3):
        for t in range(8):
            ty, tx = (t // 4) * 8, s * 32 + (t % 4) * 8
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(px[ty + y][tx + x] | px[ty + y][tx + x + 1] << 4)
    return bytes(out)


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
