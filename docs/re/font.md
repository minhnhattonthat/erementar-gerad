# Font and text rendering

## Renderer: one OBJ sprite per character cell
- Glyph lookup: `0800A51C` (codes 81xx) and `0800A86C` (other SJIS) map a big-endian SJIS code to
  (font page 0..2, glyph index). Outputs via r1 (u16 index) and r2 (u8 page).
- Glyph upload: `0800A780(page, index)`: frame table per page at 0x085D50AC / 0x085D54B0 / 0x085D58B4
  (u32 ptr per glyph -> frame header, tile number at +6), tiles at 0x0803EFB2 / 0x080479BE / 0x080503CA,
  32 bytes per 8x8 4bpp tile; uploads 0x80 bytes (16x16 sprite) via `080025C0(src, size)` -> OBJ handle.
- Dialogue layout `0800E990(x, y, str)`: per cell creates a 24-byte glyph object (array at *0x020348BC):
  x advance 0xC00 (12 px, 8.8 fixed), newline `nn` -> y += 0xE00 (14 px), auto-wrap when
  x >= (width+1)*12px (width = u16 at +0x16 of the object header). Called from 7 sites.
- Menu layout `0800E4FC(str, out)`: fills 8-byte entries {OBJ handle, u8 advance = 12}; returns count; the
  caller positions them.
- Only these two layout routines call the glyph lookups/upload.

- `080025C0(src, size)` is an OBJ tile cache keyed by the **source address**: glyphs must have distinct,
  stable source addresses (so no runtime composition into one RAM buffer).

## English (asm/pairs.asm, tools/vwf.py; spike passed 2026-10-14)
- Cell = 2 ASCII bytes drawn as one 16x16 glyph. Only pairs the script uses are pre-rendered into ROM at build
  time (PAIR_GFX, 128 B each) with a u16 lookup table PAIR_TAB[(a-0x20)*128+b]; glyph 0 = '?' fallback.
- Hooks: lookup 0800A86C (first byte < 0x80 -> page 3, idx = code), upload 0800A780 (page 3 -> PAIR_GFX),
  dialogue advance 0800EA80 and menu advance 0800E5A4 (width(a)+width(b), SJIS cells 12).
- Dialogue auto-wrap limit raised to (N+1)*12 for every cell (0800EA26): 192 px in the main box.
- `nn` stays newline: an "nn" letter pair is encoded 6E 7F (0x7F = alternate 'n').
- Font: font/en11.txt (11 px proportional, from monster-guardians), ink = palette index 1.
- Non-ASCII characters in English text stay Shift-JIS cells (game font, 12 px), aligned to a cell boundary.
