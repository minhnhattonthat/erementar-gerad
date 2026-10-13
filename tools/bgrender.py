"""Render a GBA text BG from a PPU dump (emu.py ppudump.lua files), honouring each map entry's palette and flips.

    python -X utf8 tools/bgrender.py DUMP_PREFIX BG OUT.png [--zoom 2]
DUMP_PREFIX = path without extension (…/ppu_001500); BG = 0..3. Also prints the map entries' tile range.
"""
import argparse, struct
from PIL import Image
from gfx import bgr555


def render(prefix, bg):
    vram = open(prefix + '.vram.bin', 'rb').read()
    pal = bgr555(open(prefix + '.pal.bin', 'rb').read()[:0x200])
    io = open(prefix + '.io.bin', 'rb').read()
    cnt = struct.unpack_from('<H', io, 8 + 2 * bg)[0]
    cb, sb, size = (cnt >> 2) & 3, (cnt >> 8) & 31, cnt >> 14
    w = 64 if size in (1, 3) else 32
    h = 64 if size in (2, 3) else 32
    img = Image.new('RGB', (w * 8, h * 8))
    tiles = []
    for ty in range(h):
        for tx in range(w):
            blk = (tx // 32) + (ty // 32) * (w // 32)
            e = struct.unpack_from('<H', vram, sb * 0x800 + blk * 0x800 + ((ty % 32) * 32 + tx % 32) * 2)[0]
            t, hf, vf, p = e & 0x3FF, e >> 10 & 1, e >> 11 & 1, e >> 12
            tiles.append(t)
            a = cb * 0x4000 + t * 32
            for y in range(8):
                for x in range(8):
                    sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                    v = (vram[a + sy * 4 + sx // 2] >> (4 * (sx & 1))) & 15
                    if v:
                        img.putpixel((tx * 8 + x, ty * 8 + y), pal[p * 16 + v])
    return img, cnt, tiles


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('prefix'); ap.add_argument('bg', type=int); ap.add_argument('out')
    ap.add_argument('--zoom', type=int, default=2)
    a = ap.parse_args()
    img, cnt, tiles = render(a.prefix, a.bg)
    img.resize((img.width * a.zoom, img.height * a.zoom), Image.NEAREST).save(a.out)
    nz = [t for t in tiles if t]
    print(f'BGCNT {cnt:04X}; tiles {min(nz) if nz else 0}-{max(nz) if nz else 0}')
