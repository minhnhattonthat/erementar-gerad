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
    'title_logo': (0x09C53C, 0x0181CC, [0x0181D0, 0x0181D4, 0x0181D8]),
}
WHITE, YELLOW, BLACK, PLATE = (255, 255, 255), (255, 255, 148), (0, 0, 0), (246, 246, 246)
PLATE_TEXT = [(5, 'Cou'), (53, 'Ren'), (101, 'Cisqua'), (149, 'Rowen'), (197, 'Kea')]   # battle bar, rows 6-12

# Per page: (kind, rect x0,y0,x1,y1, args). Kinds: box = white text on a flat fill (lines, optional (x, y));
# shadow = white tag-font text + black shadow on a gradient (text, x, y); badge = yellow outlined text (text).
EDITS = {
    'battle_tutorial': {
        0: [('plates', (0, 0, 0, 0), ()),
            ('box', (140, 10, 228, 30), (['A: Next'],)),
            ('box', (96, 46, 184, 78), (['Pick up', 'Select'],)),
            ('box', (22, 98, 86, 114), (['Run'],)),
            ('box', (176, 98, 236, 114), (['Item'],))],
        1: [('plates', (0, 0, 0, 0), ()),
            ('box', (140, 10, 228, 30), (['A: Next'],)),
            ('box', (22, 12, 108, 66), (['Combine them', 'to create all', 'sorts of skills'],)),
            ('box', (36, 86, 108, 100), (['button:'],)),
            ('box', (22, 102, 108, 118), (['pick a target'],)),
            ('shadow', (120, 86, 146, 96), ('Attack', 122, 88)),
            ('shadow', (130, 96, 161, 108), ('Speed', 134, 98)),
            ('badge', (194, 86, 232, 104), ('Single',))],
        2: [('plates', (0, 0, 0, 0), ()),
            ('box', (22, 12, 108, 66), (['Choose up to', '5 skills', 'per turn'],)),
            ('box', (22, 84, 108, 118), (['Press OK', 'to finish'],)),
            ('box', (140, 10, 228, 30), (['A: Fight!'],)),
            ('box', (140, 44, 228, 62), (['B: Once more'],))],
    },
    'title_logo': {
        # Rebuild the layer around the original girl and her left-hand swirl/staff.
        1: [('main_logo', (0, 0, 240, 160), ())],
        # Clear the whole Japanese subtitle, including its outline/glints at x=186 and y=111.
        2: [('subtitle', (48, 72, 192, 112), ())],
    },
}
GRADIENTS = {
    'blue': ([(255, 255, 255), (238, 246, 255), (230, 230, 246), (205, 213, 238), (189, 197, 230), (172, 180, 213),
              (156, 164, 205)], (8, 16, 24)),                        # palette-3 blues
}
# Hand-drawn native-resolution faces; never rasterize or resample a reference/font.
# Each placement is the face's top-left, leaving one pixel for the black outline.
TITLE_LOGO_ART = romlib.ROOT / 'font' / 'title-logo.txt'
TITLE_LOGO_POSITION = (2, 27)
TITLE_LOGO_SIZE = (234, 37)
TITLE_LETTERS = (
    ('outer_E_left', 3), ('L_left', 15), ('E_left', 25), ('M', 36),
    ('E_left', 49), ('N', 60), ('T', 72), ('A_left', 83), ('L_left', 95),
    ('G', 153), ('E_right', 168), ('L_right', 181), ('A_right', 193),
    ('D', 208), ('outer_E_right', 223),
)
# Shared chrome bands: upper highlight, dark middle, bright lower reflection.
# The directional dark bevel is separate from these flat, undithered face bands.
TITLE_CHROME = '88ff88667788ffff8888'
# Half-open source rectangles follow the gaps between the girl and Japanese glyphs.
# The last includes the left swirl/staff. The master extends the rod beneath GELADE;
# the original right glyph and romaji are erased.
TITLE_ICON_REGIONS = ((108, 0, 150, 45), (113, 45, 148, 57), (40, 57, 146, 75))


def parse_art(art):
    """Pixel masters use # for ink and . for transparent; retain their side bearings."""
    rows = art.strip().splitlines()
    if len({len(row) for row in rows}) != 1 or set(''.join(rows)) - {'.', '#'}:
        raise ValueError('invalid logo pixel master')
    mask = Image.new('L', (len(rows[0]), len(rows)))
    mask.putdata([255 if c == '#' else 0 for row in rows for c in row])
    return mask


def title_logo_art(palette):
    """Compose chunky angular faces, black rims, dark bevels and the original rod."""
    glyphs = {}
    for block in TITLE_LOGO_ART.read_text('ascii').strip().split('\n\n'):
        header, pixels = block.split('\n', 1)
        if not header.startswith('glyph ') or header[6:] in glyphs:
            raise ValueError(f'invalid/duplicate title glyph: {header}')
        glyphs[header[6:]] = parse_art(pixels)
    art = Image.new('RGBA', TITLE_LOGO_SIZE, (*palette[32], 0))
    ox, oy = TITLE_LOGO_POSITION

    def put(x, y, ink):
        art.putpixel((x - ox, y - oy), (*palette[32 + ink], 255))

    for name, left in TITLE_LETTERS:
        mask = glyphs[name]
        if mask.height != (20 if name.startswith('outer_') else 16):
            raise ValueError(f'invalid title glyph height: {name}')
        face = {(left + x, 39 + y) for y in range(mask.height) for x in range(mask.width)
                if mask.getpixel((x, y))}
        for x, y in face:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    put(x + dx, y + dy, 1)
        for x, y in face:
            # A continuous lower/right edge gives the heavy letters depth without
            # stippling or isolated glints. Leave the upper/left face bands flat.
            bevel = (x + 1, y) not in face or (x, y + 1) not in face
            put(x, y, 4 if bevel else int(TITLE_CHROME[y - 39], 16))
    for y, ink in ((60, 1), (61, 14), (62, 4), (63, 1)):
        for x in range(146, 234):
            put(x, y, ink)
        put(234, y, 4 if y in (61, 62) else 1)
    for y in range(58, 64):
        put(235, y, 1)
    return art


def title_logo_icon(idx, pals, palette):
    """Extract the original girl and staff, without resampling or palette conversion."""
    icon = Image.new('RGBA', (240, 160), (*palette[32], 0))
    for x0, y0, x1, y1 in TITLE_ICON_REGIONS:
        for y in range(y0, y1):
            for x in range(x0, x1):
                if idx[y][x]:
                    icon.putpixel((x, y), (*palette[pals[y // 8][x // 8] * 16 + idx[y][x]], 255))
    return icon


def draw_main_logo(img, transparent, palette, icon):
    """Erase the previous layer, then place the lettering and the exact ROM icon."""
    for y in range(img.height):
        for x in range(img.width):
            img.putpixel((x, y), transparent(x, y))
    art = title_logo_art(palette)
    img.paste(art.convert('RGB'), TITLE_LOGO_POSITION, art.getchannel('A'))
    img.paste(icon.convert('RGB'), (0, 0), icon.getchannel('A'))


# Eleven-pixel serif capitals, drawn at final resolution (no font rasterizer or rescaling).
SUBTITLE_ART = {
    'S': '.#####.\n##...##\n##....#\n##.....\n.###...\n..###..\n....###\n.....##\n#....##\n##...##\n.#####.',
    'E': '#######\n.##..##\n.##...#\n.##....\n.##.#..\n.####..\n.##.#..\n.##....\n.##...#\n.##..##\n#######',
    'A': '...##...\n..####..\n..####..\n..#.##..\n.##..##.\n.##..##.\n.######.\n##....##\n##....##\n##....##\n###..###',
    'L': '####...\n.##....\n.##....\n.##....\n.##....\n.##....\n.##....\n.##....\n.##...#\n.##..##\n#######',
    'D': '######..\n.##..##.\n.##...##\n.##...##\n.##...##\n.##...##\n.##...##\n.##...##\n.##...##\n.##..##.\n######..',
    'O': '..####..\n.##..##.\n##....##\n##....##\n##....##\n##....##\n##....##\n##....##\n##....##\n.##..##.\n..####..',
    'N': '###..###\n.###..#.\n.###..#.\n.#.##.#.\n.#.##.#.\n.#.##.#.\n.#..###.\n.#..###.\n.#...##.\n.#...##.\n###...#.',
    'G': '..#####.\n.##..###\n##.....#\n##......\n##......\n##..####\n##....##\n##....##\n##....##\n.##..###\n..####.#',
}


def clean_subtitle(img, rect, transparent):
    """Restore the transparent backdrop and ribbon before placing any English ink.

    The original subtitle is a separate BG layer: index zero reveals the title's gradient.
    Erase its *entire* footprint, including the ribbon, so no glyph, shadow or cyan glint
    survives. Reconstruct the ribbon through the areas formerly obscured by the kanji.
    """
    from PIL import ImageDraw
    x0, y0, x1, y1 = rect
    for y in range(y0, y1):
        for x in range(x0, x1):
            img.putpixel((x, y), transparent(x, y))
    dr = ImageDraw.Draw(img)
    # Tapered, tilted loop: dark rim, pearl upper edge and a blue-silver lower band.
    outer = [(82, 95), (86, 102), (97, 107), (115, 110), (138, 110), (158, 106),
             (173, 99), (182, 91), (186, 83), (184, 78), (178, 74), (164, 72),
             (147, 73), (130, 76), (113, 81), (100, 86), (92, 91), (95, 91),
             (108, 85), (124, 80), (143, 76), (161, 75), (176, 77), (181, 81),
             (180, 87), (173, 94), (160, 101), (141, 105), (120, 106), (103, 104),
             (91, 100)]
    dr.polygon(outer, fill=(8, 16, 24))
    dr.line([(96, 90), (113, 82), (131, 77), (148, 74), (164, 73), (178, 75),
             (183, 79), (184, 83)], fill=(238, 246, 255))
    dr.line([(98, 90), (114, 83), (132, 78), (148, 75), (164, 74), (176, 76)],
            fill=(82, 106, 172))
    dr.polygon([(85, 97), (92, 102), (104, 106), (120, 108), (138, 108),
                (158, 104), (172, 97), (180, 90), (183, 84), (181, 91),
                (173, 98), (158, 105), (138, 109), (115, 109), (98, 106), (88, 101)],
               fill=(156, 164, 205))
    dr.line([(92, 102), (104, 105), (120, 107), (139, 107), (158, 103), (172, 96)],
            fill=(238, 246, 255))
    dr.line([(141, 108), (158, 104), (172, 97), (180, 90), (183, 84)],
            fill=(106, 123, 189))


def draw_subtitle(img, rect, transparent):
    """Hand-letter THE / SEALED SONG over the fully cleaned subtitle background."""
    clean_subtitle(img, rect, transparent)
    mask = Image.new('L', img.size)
    small = {'T': '###\n.#.\n.#.\n.#.\n.#.', 'H': '#.#\n#.#\n###\n#.#\n#.#',
             'E': '###\n#..\n##.\n#..\n###'}
    for i, c in enumerate('THE'):
        mask.paste(parse_art(small[c]), (108 + i * 5, 80))
    glyphs = [parse_art(SUBTITLE_ART[c]) if c != ' ' else Image.new('L', (3, 11))
              for c in 'SEALED SONG']
    width = sum(g.width for g in glyphs) + 2 * (len(glyphs) - 1)
    x = 114 - width // 2
    for glyph in glyphs:
        mask.paste(glyph, (x, 89))
        x += glyph.width + 2
    ink = {(x, y) for y in range(rect[1], rect[3]) for x in range(rect[0], rect[2])
           if mask.getpixel((x, y))}
    edge = (8, 16, 24)
    for x, y in ink:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (x + dx, y + dy) not in ink:
                    img.putpixel((x + dx, y + dy), edge)
    grad = GRADIENTS['blue'][0]
    for x, y in ink:
        row = y - (80 if y < 89 else 89)
        # Pearl face with a bright upper bevel; the lower strokes shade to periwinkle.
        shade = min(6, row * 7 // (5 if y < 89 else 11))
        if (x, y - 1) not in ink:
            shade = 0
        img.putpixel((x, y), grad[shade])


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


def edit_page(img, edits, transparent=None, palette=None, title_icon=None):
    """transparent(x, y) -> colour of palette index 0 for the tile at x, y (title erase target)."""
    font, tf = vwf.Font(), tag_font()
    grey = lambda c: c[0] == c[1] == c[2]
    orig = img.copy()
    plates = PLATE_TEXT if any(k == 'plates' for k, *_ in edits) else []
    for t0 in plates:          # battle bar names (only pixels that were the bar's greys, so boxes stay)
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
        elif kind == 'plates':
            pass   # handled above
        elif kind == 'main_logo':
            draw_main_logo(img, transparent, palette, title_icon)
        elif kind == 'subtitle':
            draw_subtitle(img, (x0, y0, x1, y1), transparent)
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


def render_page(tiles, m, pal, edits):
    """Render edits with their palette banks; return the image and encoding grids."""
    idx, pals = page_indices(tiles, m)
    img = to_img(idx, pals, pal)
    title_icon = None
    for kind, (x0, y0, x1, y1), _ in edits:
        if kind == 'main_logo':
            title_icon = title_logo_icon(idx, pals, pal)
            # Preserve the icon's exact indices and tile banks (1 above y=48, 2
            # below). Lettering fits outside its bank-1 tiles and uses silver bank 2.
            for ty in range(20):
                for tx in range(30):
                    if not title_icon.crop((tx * 8, ty * 8, tx * 8 + 8, ty * 8 + 8)).getbbox():
                        pals[ty][tx] = 2
            for y in range(160):
                for x in range(240):
                    if not title_icon.getpixel((x, y))[3]:
                        idx[y][x] = 0
        elif kind == 'subtitle':
            # The old text mixes banks 3/4 and blank bank-0 tiles. Its replacement uses
            # the existing blue bank throughout the fully erased, tile-aligned area.
            assert all(v % 8 == 0 for v in (x0, y0, x1, y1))
            for ty in range(y0 // 8, y1 // 8):
                for tx in range(x0 // 8, x1 // 8):
                    pals[ty][tx] = 3
    edit_page(img, edits, lambda x, y: pal[pals[y // 8][x // 8] * 16], pal, title_icon)
    return img, idx, pals


def encode(d, name):
    """-> (tileset bytes, [map bytes]) for the English pages."""
    pal, tiles, maps = load(d, name)
    out_tiles, seen, new_maps = [bytes(32)], {bytes(32): 0}, []
    for page, m in enumerate(maps):
        img, idx, pals = render_page(tiles, m, pal, EDITS.get(name, {}).get(page, []))
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
                        elif min(sum(abs(a - b) for a, b in zip(c, k)) for k in colors) <= 50:
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
                render_page(tiles, m, pal, EDITS.get(name, {}).get(i, []))[0].save(out / f'{name}_{i}_en.png')
                print(out / f'{name}_{i}_en.png')
