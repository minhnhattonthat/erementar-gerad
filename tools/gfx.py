"""Small 4bpp tile helpers for graphics-text work (docs/re/graphics.md).

    python -X utf8 tools/gfx.py tags OUT.png      render every dialogue name tag (48x16) from the original ROM
"""
import sys
from PIL import Image
import romlib

TAG_BASE, TAG_STRIDE, TAG_SIZE = 0x251D34, 0x400, 0x180   # name tag n at TAG_BASE + (n+1)*0x400; "???" at 0x2522B4


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
    if sys.argv[1] == 'tags':
        n = 40
        sheet = Image.new('RGB', (48 * 4 + 12, 18 * ((n + 4) // 4)))
        for i in range(-1, n - 1):
            a = TAG_BASE + (i + 1) * TAG_STRIDE if i >= 0 else 0x2522B4
            img = tiles_to_img(d[a:a + TAG_SIZE], 6, 2)
            k = i + 1
            sheet.paste(img, ((k % 4) * 51, (k // 4) * 18))
        sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(sys.argv[2])
