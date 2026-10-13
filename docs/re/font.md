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

## English plan (engine spike pending)
- Cell = 2 ASCII bytes (both letters drawn in one 16x16 sprite). Hook lookup: first byte < 0x80 -> page 3 =
  "pair" glyph; hook upload: compose the pair from a proportional 1bpp font into a RAM buffer, upload that.
- Variable advance: dialogue x += width(pair) instead of 12; menu entry advance byte = width(pair).
  Same sprite count per line as Japanese (~20), ~2x the letters.
- `nn` stays newline: the encoder must never place "nn" letters in one cell (swap in an alternate 'n' code).
