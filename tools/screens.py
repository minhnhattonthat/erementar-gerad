"""Full-screen LZ77 pictures (tutorial pages etc.): decode, English redraw, re-encode (docs/re/graphics.md).

    python -X utf8 tools/screens.py export NAME|all      -> work/screens/<name>_<page>.png (+ _en.png redraws)
A screen = BG palettes + one LZ77 4bpp tileset + LZ77 32x32-entry tilemaps (one per page); the pointers sit in code
literal pools (SCREENS). The build re-encodes edited pages into a new tileset + maps in free space and repoints.
"""
import collections, struct, sys
from PIL import Image
import lz77, romlib, vwf
from gfx import bgr555, tag_font

# name: (palette offset, tileset pointer slot, [map pointer slots])
SCREENS = {
    'battle_tutorial': (0x09C97C, 0x01BBB8, [0x01BBBC, 0x01BBC0, 0x01BBC4]),
}
WHITE, YELLOW, BLACK, PLATE = (255, 255, 255), (255, 255, 148), (0, 0, 0), (246, 246, 246)
PLATE_TEXT = [(5, 'Cou'), (53, 'Ren'), (101, 'Cisqua'), (149, 'Rowen'), (197, 'Kea')]   # battle bar, rows 6-12

# Per page: (kind, rect x0,y0,x1,y1, args). Kinds: box = white text on a flat fill (lines, optional (x, y));
# shadow = white tag-font text + black shadow on a gradient (text, x, y); badge = yellow outlined text (text).
EDITS = {
    'battle_tutorial': {
        0: [('box', (140, 10, 228, 30), (['A: Next'],)),
            ('box', (96, 46, 184, 78), (['Pick up', 'Select'],)),
            ('box', (22, 98, 86, 114), (['Run'],)),
            ('box', (176, 98, 236, 114), (['Item'],))],
        1: [('box', (140, 10, 228, 30), (['A: Next'],)),
            ('box', (22, 12, 108, 66), (['Combine them', 'to create all', 'sorts of skills'],)),
            ('box', (36, 86, 108, 100), (['button:'],)),
            ('box', (22, 102, 108, 118), (['pick a target'],)),
            ('shadow', (120, 86, 146, 96), ('Attack', 122, 88)),
            ('shadow', (130, 96, 161, 108), ('Speed', 134, 98)),
            ('badge', (194, 86, 232, 104), ('Single',))],
        2: [('box', (22, 12, 108, 66), (['Choose up to', '5 skills', 'per turn'],)),
            ('box', (22, 84, 108, 118), (['Press OK', 'to finish'],)),
            ('box', (140, 10, 228, 30), (['A: Fight!'],)),
            ('box', (140, 44, 228, 62), (['B: Once more'],))],
    },
}


def ptr(d, slot):
    return struct.unpack_from('<I', d, slot)[0] - romlib.BASE


def load(d, name):
    """-> (palette, tileset bytes, [map bytes])."""
    pal_at, ts_slot, map_slots = SCREENS[name]
    pal = bgr555(d[pal_at:pal_at + 0x200])
    tiles = lz77.decompress(d, ptr(d, ts_slot))[0]
    maps = [lz77.decompress(d, ptr(d, s))[0] for s in map_slots]
    return pal, tiles, maps


def tile_px(tiles, t):
    a = t * 32
    return [[(tiles[a + y * 4 + x // 2] >> (4 * (x & 1))) & 15 if a < len(tiles) else 0 for x in range(8)]
            for y in range(8)]


def page_indices(tiles, m):
    """-> (index grid 160x240, palette grid 20x30)."""
    idx = [[0] * 240 for _ in range(160)]
    pals = [[0] * 30 for _ in range(20)]
    for ty in range(20):
        for tx in range(30):
            e = struct.unpack_from('<H', m, (ty * 32 + tx) * 2)[0]
            t, hf, vf, p = e & 0x3FF, e >> 10 & 1, e >> 11 & 1, e >> 12
            pals[ty][tx] = p
            px = tile_px(tiles, t)
            for y in range(8):
                for x in range(8):
                    idx[ty * 8 + y][tx * 8 + x] = px[7 - y if vf else y][7 - x if hf else x]
    return idx, pals


def to_img(idx, pals, pal):
    img = Image.new('RGB', (240, 160))
    for y in range(160):
        for x in range(240):
            img.putpixel((x, y), pal[pals[y // 8][x // 8] * 16 + idx[y][x]])
    return img


def draw_glyphs(img, text, x, y, color, font, mask=None):
    for c in text:
        for (gx, gy) in font.px[ord(c)]:
            if mask is None or mask(x + gx, y + gy):
                img.putpixel((x + gx, y + gy), color)
        x += font.w[ord(c)]


def edit_page(img, edits):
    font, tf = vwf.Font(), tag_font()
    grey = lambda c: c[0] == c[1] == c[2]
    orig = img.copy()
    for t0 in PLATE_TEXT:          # battle bar names (only pixels that were the bar's greys, so boxes stay)
        x0, name = t0
        for y in range(6, 13):
            for x in range(x0, x0 + 30):
                c = orig.getpixel((x, y))
                if grey(c) and sum(c) > 400:
                    img.putpixel((x, y), BLACK)
        x = x0
        for c in name:
            for gy, row in enumerate(tf[c]):
                for gx, on in enumerate(row):
                    if on and grey(orig.getpixel((x + gx, 6 + gy))):
                        img.putpixel((x + gx, 6 + gy), PLATE)
            x += len(tf[c][0]) + 1
    for kind, (x0, y0, x1, y1), args in edits:
        if kind == 'box':
            fill = collections.Counter(img.getpixel((x, y)) for x in range(x0, x1) for y in range(y0, y1)
                                       if img.getpixel((x, y)) != WHITE).most_common(1)[0][0]
            for y in range(y0, y1):
                for x in range(x0, x1):
                    if img.getpixel((x, y)) == WHITE:
                        img.putpixel((x, y), fill)
            lines = args[0]
            top = y0 + (y1 - y0 - 14 * len(lines)) // 2 + 1
            for i, line in enumerate(lines):
                if font.text_width(line) > x1 - x0:
                    raise ValueError(f'{line!r} wider than its box ({x1 - x0} px)')
                draw_glyphs(img, line, x0 + 1, top + 14 * i, WHITE, font)
        elif kind in ('shadow', 'badge'):
            ink_colors = (WHITE, BLACK, PLATE) if kind == 'shadow' else (YELLOW, BLACK)
            for y in range(y0, y1):
                for x in range(x0, x1):
                    if img.getpixel((x, y)) in ink_colors:   # background = that row's colour within the same tile
                        tx = x // 8 * 8
                        bg = collections.Counter(c for c in (img.getpixel((i, y)) for i in range(tx, tx + 8))
                                                 if c not in ink_colors).most_common(1)
                        if bg:
                            img.putpixel((x, y), bg[0][0])
            if kind == 'shadow':
                text, x, y = args
                ink = set()
                for c in text:
                    for gy, row in enumerate(tf[c]):
                        for gx, on in enumerate(row):
                            if on:
                                ink.add((x + gx, y + gy))
                    x += len(tf[c][0]) + 1
                for (ix, iy) in ink:
                    for s in ((ix + 1, iy), (ix, iy + 1), (ix + 1, iy + 1)):
                        if s not in ink:
                            img.putpixel(s, BLACK)
                for p in ink:
                    img.putpixel(p, WHITE)
            else:
                from gfx import outlined
                px = outlined(font, args[0], x1 - x0, y1 - y0, 0, x1 - x0, y0=3, tight=True, fill=2, edge=1)
                for y in range(y1 - y0):
                    for x in range(x1 - x0):
                        if px[y][x]:
                            img.putpixel((x0 + x, y0 + y), YELLOW if px[y][x] == 2 else BLACK)
    return img


def encode(d, name):
    """-> (tileset bytes, [map bytes]) for the English pages."""
    pal, tiles, maps = load(d, name)
    out_tiles, seen, new_maps = [bytes(32)], {bytes(32): 0}, []
    for page, m in enumerate(maps):
        idx, pals = page_indices(tiles, m)
        img = edit_page(to_img(idx, pals, pal), EDITS.get(name, {}).get(page, []))
        nm = bytearray(m)
        for ty in range(20):
            for tx in range(30):
                p = pals[ty][tx]
                colors = pal[p * 16:p * 16 + 16]
                t = bytearray()
                for y in range(8):
                    row = []
                    for x in range(8):
                        c, o = img.getpixel((tx * 8 + x, ty * 8 + y)), idx[ty * 8 + y][tx * 8 + x]
                        if colors[o] == c:
                            row.append(o)
                        elif c in colors:
                            row.append(colors.index(c))
                        elif c == PLATE:   # bar name running under a box: keep the box's own pixel
                            row.append(o)
                        elif min(sum(abs(a - b) for a, b in zip(c, k)) for k in colors) <= 40:
                            # tiles under the same art use slightly different whites (255 vs 246): nearest
                            row.append(min(range(16), key=lambda i: sum(abs(a - b) for a, b in zip(c, colors[i]))))
                        else:
                            raise ValueError(f'{name} page {page}: colour {c} not in palette {p} at tile {tx},{ty}')
                    for x in range(0, 8, 2):
                        t.append(row[x] | row[x + 1] << 4)
                t = bytes(t)
                if t not in seen:
                    seen[t] = len(out_tiles)
                    out_tiles.append(t)
                struct.pack_into('<H', nm, (ty * 32 + tx) * 2, seen[t] | p << 12)
        new_maps.append(bytes(nm))
    if len(out_tiles) > 1024:
        raise ValueError(f'{name}: {len(out_tiles)} tiles > 1024')
    return b''.join(out_tiles), new_maps


def patches(d, put):
    """Re-encode every screen with edits; put(bytes) -> offset in free space. -> [(slot, new pointer value)]."""
    out = []
    for name, (pal_at, ts_slot, map_slots) in SCREENS.items():
        if name not in EDITS:
            continue
        ts, maps = encode(d, name)
        out.append((ts_slot, put(lz77.compress(ts))))
        for s, m in zip(map_slots, maps):
            out.append((s, put(lz77.compress(m))))
    return out


if __name__ == '__main__':
    d = romlib.load()
    out = romlib.ROOT / 'work' / 'screens'
    out.mkdir(parents=True, exist_ok=True)
    if sys.argv[1] == 'export':
        for name in (SCREENS if sys.argv[2] == 'all' else [sys.argv[2]]):
            pal, tiles, maps = load(d, name)
            for i, m in enumerate(maps):
                idx, pals = page_indices(tiles, m)
                img = to_img(idx, pals, pal)
                img.save(out / f'{name}_{i}.png')
                edit_page(img, EDITS.get(name, {}).get(i, [])).save(out / f'{name}_{i}_en.png')
                print(out / f'{name}_{i}_en.png')
