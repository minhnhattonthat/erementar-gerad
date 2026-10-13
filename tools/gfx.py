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
    if sys.argv[1] == 'tags-en':
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
