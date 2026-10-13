# Text

## Encoding
- Shift-JIS (cp932), NUL-terminated C strings, starts 4-aligned (rodata), padded with 00.
- Every character cell is 2 bytes; the renderers step 2 bytes per cell and test only the first byte for NUL.
- Only control code seen in script text: `nn` (6E 6E) = newline. No inline variables: names/numbers are drawn
  by code as separate strings.
- Full-width space 8140 is special-cased by the script engine (a string that is exactly "　" = empty line).

## Where strings live
| Range | What | Referenced from |
|---|---|---|
| 0x0386xx–0x03Dxxx | menu/shop/item/system strings (rodata next to code) | code literal pools, item table 0x03D258 (stride 0x24) |
| 0x0B3xxx–0x0B8Cxx | debug menu labels, combo-skill descriptions | table 0x0B9A04 (stride 0x3C), code |
| 0x1F2000–0x23Dxxx | event/dialogue script strings (data blocks interleaved: 0x1F36xx, 0x23Dxxx+ graphics) | script records 0x5D0000–0x63CB7B |

## Script records (0x5D0000–0x63CB7B)
- Interpreter (e.g. 0x08026F88, 0x08028C3C) indexes `base + i*36`; string pointer at record +0x10.
- The region also holds other tables (stride 32 at 0x5D38D0, font frame tables at 0x5D50AC/54B0/58B4).
- ~952 distinct pointers into the region come from code (0x10000–0x2B000), tables at 0x1F3000–0x1F4FFF,
  0x37E000 and inside the region itself.

## Pointer slots
- Aligned u32 `0x08000000|off` pointing at a string start.
- Words in 0x370000–0x5C0000 that equal text addresses are coincidences (graphics); never patch them.
- Slot rule used by the extractor: slot in code/rodata (<0x0C0000), 0x1F0000 tables or the script region,
  target is a NUL-preceded string whose cells are all SJIS double-byte or `nn`.

## Draw-hook
- `tools/lua/textcalls.lua` logs callers of the glyph lookups and the dialogue layout routine.
