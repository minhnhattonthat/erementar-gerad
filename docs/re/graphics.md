# Graphics text survey (tile-drawn Japanese)

| # | Element | Where seen | Layer | Source | Status |
|---|---|---|---|---|---|
| 1 | Dialogue name tags (16: ???, クー, レン, ローウェン, キーア, シスカ, ヴォルクス, チルル, ショウニン, エンダ, カールセン, アークエイルイン, カメンノオトコ, オバーチャン, オジーチャン, シンプ) | every dialogue | BG0 tiles 160-171 (VRAM 0x06001400), 48x16 | raw 4bpp at 0x251D34 + (speaker+1)*0x400 (0x180 B each), "???" at 0x2522B4; copied by 0x08028756/0x08028770 | todo: redraw; white text + dark shadow on pink, ~8 px tall -> needs a compact font |
| 2 | Item list labels (傷薬 x05 ...) | menu > item | OBJ, 3x 32x16 per row (96x16) | raw 4bpp ~0x1E1D00-0x1E3A00 (vramfind) | todo |
| 3 | Item info: 回復 / スピード / 単体 | menu > item | OBJ (right panel) | ? | todo |
| 4 | Character tabs (クー レン シスカ ローウェン キーア) | menu bottom | OBJ? (BG1 has empty tab frames) | ? | todo |
| 5 | Battle UI: にげる (L), アイテム (R) | battle | ? | ? | todo |
| 6 | Title logo エレメンタルジェレイド 封印されし謳 | title | BG | ? (likely compressed) | todo |
| 7 | Status screen HP/ATK/SPD/DEF/EXP/NEXT/Lv | menu > status | BG | already English | ok |
| 8 | Map "MORNING" etc., PRESS START / NEW GAME | map, title | | already English | ok |

Notes
- 0x1E0000-0x1E1C00 holds a small kana tile font (seen in tiles.py render) - find its user (battle messages?).
- Debug screens (mode_debug, BG text 0x08008C0C) stay Japanese/fullwidth: developer-only.
