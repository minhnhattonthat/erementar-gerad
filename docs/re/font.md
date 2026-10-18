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

## Menu layout newline
- 0800E4FC turns an `nn` cell into an empty entry (handle 0 = draw does x reset, y += 14) and branches to the loop
  tail 0800E5AA, inside the menu_advance hook; the hook keeps a valid tail at E5AC (newline_tail) and E54C points
  there. Before this fix every multi-line menu string (save/load Yes\nNo) lost everything after the first line.

## List menus (builder 0801162C, item init 08011384.., draw 08011560..)
- Item = {glyph entries, u16 cell count, ..}, buffer sized from the count (no overflow). The draw centred each item
  on x+40 at 12 px per cell (08011572); pairs.asm menu_x centres on the summed entry advances. Map menu
  View/Menu/Save/Enter = table 0x03C5B0 {string, handler}.

## Choice options (task_adv_menuTabList, class 0x085D9A58: name, init 08029854, update, draw 08029BAC, free, size)
- One object per option row; menu layout 0800E4FC fills a glyph-entry buffer at +0x44 that holds 8 cells and
  overflows into +0x84.. (longer options vanished or broke the row). pairs.asm moves the buffer to +0x98, sized
  CHOICE_CELLS (16), by growing the class size word at 0x085D9A6C.
- Draw centres the row from the cell count (+0x88): side 0 x+40, side 1 x+64 minus 6 px per cell. Hook choice_x
  centres on the summed entry advances instead (the string pointer at +0x94 is shared by all rows by draw time).
- Width budget: tools/lint.py CHOICE_W = 96 px; choice strings found by heuristic (record +0x23 = 0x10 jump label,
  Japanese one line <= 8 cells). QA state before the first choice: from the battle result, mash A ~3000 frames.
