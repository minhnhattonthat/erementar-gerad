# Graphics text survey (tile-drawn Japanese)

| # | Element | Where seen | Layer | Source | Status |
|---|---|---|---|---|---|
| 1 | Dialogue name tags (16) | every dialogue | BG0 tiles 160-171 (VRAM 0x06001400), 48x16 | raw 4bpp 0x251D34 + (speaker+1)*0x400 (0x180 B), "???" at 0x2522B4 | DONE: gfx.tag_patches, font/tag.txt |
| 2 | Combo skill labels (201) + reading line (96x8) | battle combo info, skill list | OBJ 3x 32x16 | table 0x0C1830: (label 0x300 B, reading 0x180 B) pairs; descriptions via 0x0B99E0+0x14*i (+0x10) | font/labels.tsv C000-C200 (agent), gfx.label_patches; readings blanked |
| 3 | Enemy attack labels (56) | battle | OBJ 96x16 | table 0x5D6DA8 (56 ptrs) | font/labels.tsv A000-A055 |
| 4 | Item labels (10) | menu > item, battle item | OBJ 96x16 | table 0x0C1760 (+0x14*i, ptr at +0x10) | font/labels.tsv I000-I009 |
| 5 | Item/combo info: 回復 / 攻撃 / スピード / 単体 / 全体 | menu > item, battle info box | OBJ | raw around 0x19BDFC-0x19C63B and 0x08D91C (vramfind) | todo |
| 6 | Menu character tabs (クー レン シスカ ローウェン キーア) | menu bottom | OBJ 5x 32x16 (y=141) | raw 0x08DBDC-0x08E0DB | todo |
| 7 | Battle HP-bar name plates (same 5 names) | battle top | ? | ? (likely near #6) | todo |
| 8 | Battle UI: にげる (L), アイテム (R) | battle | ? | ? | todo |
| 9 | Title logo エレメンタルジェレイド 封印されし謳 | title | BG | ? (likely compressed) | todo |
| 10 | Tiny katakana font (5px) at 0x08C200 | ? (unknown user) | | raw | investigate |
| 11 | Status HP/ATK/SPD/DEF/EXP/NEXT/Lv, map MORNING, PRESS START / NEW GAME | | | already English | ok |

Notes
- Debug screens (mode_debug, BG text 0x08008C0C) stay Japanese/fullwidth: developer-only.
- Debug menu entry: tools/lua/debugmenu.lua (EVENT = prologue, BATTLE = direct battles, useful for QA).
