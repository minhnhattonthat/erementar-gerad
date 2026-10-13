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
| 7 | Battle HP-bar name plates | battle top | OBJ 32x8 | raw 0x0C45F8 (27 tiles) | DONE (plate_patches) |
| 8 | Battle tutorial (3 pages: にげる/アイテム/ピックアップ/...) | first battle | BG3 full-screen picture | LZ77 tileset 0x0AC700 + maps 0x0B2240/0B261C/0B2A48, pal 0x09C97C; slots 0x01BBB8.. | DONE (screens.py) |
| 9 | Title logo エレメンタルジェレイド + subtitle 封印されし謳 | title | BG full-screen pictures | screen sets slot 0x0181CC (logo pages 0x181D0-0x181D8, pal 0x9C53C) and 0x019B50 (subtitle, pal 0x9B75C) | todo |
| 12 | Enemy name tags (30) above attack banners | battle | OBJ 48x8 | 0x1D5DBC + 0xC0*k (enemy records 0x0B55E0, 0x24 B, +4 ptr) | DONE (enemy_tag_patches); readings of fantasy names unsure: ヒューカス Hyukas, ビルニト Birnit, ディバイパー Diviper, コーモース Komos, ディシャス Dishas, ラグナント Ragnant, ブラブレス Brabless, ガリドリー Garidley, モルニール Molnir, ラーダ Rada, ムスキーブ Muskib, ガラウコロウ Garaukorou, ガライビン Garaibin, ラウ Rau, ディオス Dios |
| 10 | Orange name plates (レン, キーア...) in the tile pool 0x19C83C tiles 44-67, big glyph pieces 69-107 | ? (combo cut-ins?) | OBJ composites | pool | investigate where shown |
| 11 | Tiny katakana font (5px) at 0x08C200 | ? (unknown user) | | raw | investigate |

All 12 LZ77 screen sets found by scanning code literal pools (tileset + 0x500 maps): forest/town backgrounds, menu
frames, arena RANK board, TOMY/jupiter logos - no other Japanese.
| 11 | Status HP/ATK/SPD/DEF/EXP/NEXT/Lv, map MORNING, PRESS START / NEW GAME | | | already English | ok |

Notes
- Debug screens (mode_debug, BG text 0x08008C0C) stay Japanese/fullwidth: developer-only.
- Debug menu entry: tools/lua/debugmenu.lua (EVENT = prologue, BATTLE = direct battles, useful for QA).
