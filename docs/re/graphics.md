# Graphics text survey (tile-drawn Japanese)

| # | Element | Where seen | Layer | Source | Status |
|---|---|---|---|---|---|
| 1 | Dialogue name tags (16) | every dialogue | BG0 tiles 160-171 (VRAM 0x06001400), 48x16 | raw 4bpp 0x251D34 + (speaker+1)*0x400 (0x180 B), "???" at 0x2522B4 | DONE: gfx.tag_patches, font/tag.txt |
| 2 | Combo skill labels (201) + reading line (96x8) | battle combo info, skill list | OBJ 3x 32x16 | table 0x0C1830: (label 0x300 B, reading 0x180 B) pairs; descriptions via 0x0B99E0+0x14*i (+0x10) | font/labels.tsv C000-C200 (agent), gfx.label_patches; readings blanked |
| 3 | Enemy attack labels (56) | battle | OBJ 96x16 | table 0x5D6DA8 (56 ptrs) | font/labels.tsv A000-A055 |
| 4 | Item labels (10) | menu > item, battle item | OBJ 96x16 | table 0x0C1760 (+0x14*i, ptr at +0x10) | font/labels.tsv I000-I009 |
| 5 | Info headers 回復/攻撃/スピード | item box, battle combo box | OBJ composites built in VRAM from the 8x8 tile pool 0x19C83C (116 tiles) | gfx.COMPOSITES (layouts from VRAM dumps) | DONE |
| 5b | Badges 全体/単体; status labels リアクト/状態異常/行動不能/戦闘不能 | info boxes, battle | OBJ 32x16 | 0x19C23C/0x19C33C; 0x19C43C + 0x100*k | DONE (badge_patches, status_patches) |
| 6 | Menu character tabs | menu bottom | OBJ 5x 32x16 | raw 0x08DBDC (0x100 each) | DONE (tab_patches) |
| 7 | Battle HP-bar name plates | battle top | OBJ 32x8 | raw 0x0C45F8 (27 tiles) + combined plates クー&レン / ローウェン&キーア (tiles 27-32, 39-46, ink 3) | DONE (plate_patches) |
| 7c | Map place-name plates (16: 南の森 .. カールセンの家, ???) | world map, bottom right | OBJ frames | frame table 0x5D6218 (u32 -> {n, n x attr0/1/2, 0}), tiles sheet 0x6399A | DONE (map_name_patches: tiles redrawn, frames rebuilt in free space; ??? kept) |
| 7b | Battle result name boxes (5 + a second クー at 0x19957C, use unknown) | battle result | OBJ 32x16 | raw 0x19967C + 0x100*i | DONE (result_box_patches) |
| 8 | Battle tutorial (3 pages: にげる/アイテム/ピックアップ/...) | first battle | BG3 full-screen picture | LZ77 tileset 0x0AC700 + maps 0x0B2240/0B261C/0B2A48, pal 0x09C97C; slots 0x01BBB8.. | DONE (screens.py) |
| 9 | Title logo エレメンタルジェレイド + subtitle 封印されし謳 | title | BG full-screen pictures | tileset slot 0x0181CC, maps 0x0181D0-0x0181D8, pal 0x09C53C; subtitle is the third map (0x0181D8) | DONE (screens.py + font/title-logo.txt): bold, angular ELEMENTAL / GELADE following the official lettering; black rims plus dark lower/right bevels, shared chrome bands, open counters; aligned tops and descending outer E's; exact JP girl/left swirl/staff and THE / SEALED SONG; rod reaches last E; weight, artwork, shading, spacing, counter and fragment gates; cold-boot Mesen logo7 QA + lettering-only comparison |
| 12 | Enemy name tags (30) above attack banners | battle | OBJ 48x8 | 0x1D5DBC + 0xC0*k (enemy records 0x0B55E0, 0x24 B, +4 ptr) | DONE (enemy_tag_patches); readings of fantasy names unsure: ヒューカス Hyukas, ビルニト Birnit, ディバイパー Diviper, コーモース Komos, ディシャス Dishas, ラグナント Ragnant, ブラブレス Brabless, ガリドリー Garidley, モルニール Molnir, ラーダ Rada, ムスキーブ Muskib, ガラウコロウ Garaukorou, ガライビン Garaibin, ラウ Rau, ディオス Dios |
| 10 | Orange name plates (レン, キーア...) in the tile pool 0x19C83C tiles 44-67, big glyph pieces 69-107 | ? (combo cut-ins?) | OBJ composites | pool | investigate where shown |
| 11 | Tiny katakana font (5px) at 0x08C200 | ? (unknown user) | | raw | investigate |

All 12 LZ77 screen sets found by scanning code literal pools (tileset + 0x500 maps): forest/town backgrounds, menu
frames, arena RANK board, TOMY/jupiter logos - no other Japanese.
| 11 | Status HP/ATK/SPD/DEF/EXP/NEXT/Lv, map MORNING, PRESS START / NEW GAME | | | already English | ok |

Notes
- Main title redesign (2026-10-19, logo7): **ELEMENTAL** left of the original JP girl, **GELADE** right.
  Follow-up to logo6: match the official anime lettering's weight and angular details while retaining
  clean native-resolution pixels. Shorter, blocky faces use three/four-pixel stems and bars, slanted E
  spurs, notched M/N diagonals, angled A caps, hooked G/L shapes and a sharply cut D bowl.
  `font/title-logo.txt` stores named glyph masks (`#` face, `.` transparent); `screens.title_logo_art`
  composes them without font rasterization or scaling. A one-pixel black rim plus an inner dark
  lower/right bevel (bank-2 index 4) gives each heavy face a two-pixel dark edge on its shaded sides.
  One transparent column between outlined letters keeps every glyph distinct. A/D counters,
  E apertures and G's mouth remain open. All outlined tops align at y=38; 16-row normal faces end
  with their outline at y=55, and the 20-row outer E faces descend to y=59 (no upward extension).
  Every face uses the same chrome bands: bank-2 indices 8/f/8/6/7/8, two rows each at y=39..50,
  then f at y=51..54 and 8 at y=55..58. Four stepped shades create a bright upper highlight,
  dark middle and light lower reflection without dithering or isolated glints. The directional bevel
  stays continuous around lower/right face edges. The canvas remains 234x37 at `(2,27)`.
  The glyph file is the build input: no dependency on the gitignored anime reference or `work/`.
  Extract the girl and left swirl/staff directly from the JP ROM's second map using half-open regions
  `(108,0)-(150,45)`, `(113,45)-(148,57)`, `(40,57)-(146,75)`: **2,222 opaque pixels**, unchanged
  positions, indices and tile palette banks (1 above y=48, 2 below). The mask follows the gaps around
  the Japanese glyphs. Preserve its transparent holes too; no retracing, rescaling or recolouring.
  Erase the full 240x160 layer before compositing the stored letters and extracted icon. Remove the
  Japanese lettering and the separate small `EREMENTAR GERAD` caption. The master extends the rod
  from x=146 through x=235 at y=60..63, beneath GELADE to its last E: bank-2 indices 1/e/4/1
  match the original rod's black rim, bright highlight and dark underside, with a closed end cap
  joined to the last E. The original girl and left swirl/staff mask, including its holes, stays exact.
  No palette edits or antialiasing. The first map and approved third-map subtitle remain pixel-identical.
  Rebuilt title set: **190 tiles** (original 230), **3064 B LZ77 tileset** (original 4635 B, 4636 padded),
  three unchanged 0x500-byte map lengths; compressed maps 220/416/280 B (original 228/464/324 B).
  `tests/test_screens.py` gates `tools/check.py` with exact decoded-map comparisons to the stored design
  and updated `tests/fixtures/title_logo.png` (RGB plus transparency), independent original-ROM icon
  comparisons and indexed hash, every letter's top/baseline and descending E heights, rod shading/end-cap
  assertions, flat shared chrome bands, exact black rims and dark bevels, spacing and open counters.
  Decoded faces must fill at least 52% of each glyph box and have a three-pixel run on every row;
  each face/bevel must also form one four-connected component, rejecting flecks inside a connected rim.
  Caption removal,
  connected-component fragment checks, fully poisoned-layer cleanup, unchanged subtitle RGB/index
  hashes and allocation limits remain gated. The chrome test also rejects single-pixel face strokes.
  Check: 14 tests passed, lint 0 errors (226 existing glossary warnings); build passed. Cold-boot Mesen:
  1500 frames, ten shots, smoke passed; `work/qa/logo7/final.png`, `sheet.png`, `logo-zoom.png`
  (4x crop `(0,0)-(240,116)`, inspected: aligned E tops, clear lettering and no stray pixels).
  `work/qa/logo7/compare.png` places reference lettering beside decoded built-ROM lettering at the
  same 88-pixel displayed height, omitting both centre icons and staffs. Compared visually: heavier
  silhouettes, angular cuts and dark bevels approach the reference while the narrower left word stays
  readable beside the unmodified girl. `python -X utf8 tools/logo_compare.py work/qa/logo7` regenerates
  both review images from the supplied reference, built ROM and cold-boot capture (QA only, not a build input).
- Title subtitle (2026-10-19): erase the complete tile-aligned `(48,72)-(192,112)` region to transparency
  before reconstructing the ribbon and drawing the English. Original nonzero pixels extend through x=186,
  y=111, outside the former erase rectangle. Palette bank 3 supplies the English face, shading and outline;
  index zero reveals the original title background. The other two title maps render pixel-identically to
  the preceding logo work. At subtitle approval: 213 tiles (original 230), LZ77 tileset 3560 B (original 4636 B),
  three unchanged 0x500-byte map lengths. QA: `work/qa/subtitle/final.png`, `sheet.png`, `subtitle-zoom.png`.
- Correction to the former row 9: slot 0x019B50 / map 0x019B54 / palette 0x09B75C is an **8bpp character/menu
  background**, not the title subtitle; decoding it shows a character at right and list rows at left.
- Debug screens (mode_debug, BG text 0x08008C0C) stay Japanese/fullwidth: developer-only.
- Debug menu entry: tools/lua/debugmenu.lua (EVENT = prologue, BATTLE = direct battles, useful for QA).
