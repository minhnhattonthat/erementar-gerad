# Label brief - Erementar Gerad (GBA): skill / attack / item name graphics

The game shows skill, enemy-attack and item names as pre-rendered 96x16 images (no text strings exist for them).
Your job: read each Japanese label from the sheets, translate it, and write the English the build will draw.
Repo root: H:/translation/erementar-gerad. Do all work yourself; do not dispatch subagents.

## Inputs
- `work/labels/sheet_00.png` ... `sheet_07.png`: rows of `KEY | label (Japanese, white) | reading line`. Keys:
  - `C000-C200`: party combination skills (Pledger + Edel Raid combos). The right column is the official katakana
    reading shown under the label; it is often an English loanword (トライアングル = Triangle, レッドリンクス = Red Lynx).
  - `A000-A055`: enemy attacks (no reading).
  - `I000-I009`: items (no reading).
- `work/labels/labels.tsv`: `KEY<TAB>context` - for C keys the in-game skill description (Japanese), for others a type.
- `script/sys.json`: item names (ids 03D01C 傷薬, 03D048 上傷薬, 03D07C, 03D0B4, 03D0E4, 03D120, 03D158, 03D190, 03D1B8,
  03D1F0 in I000-I009 order) and skill descriptions; use any `en` already there so labels match the text.
- `glossary.md` (names/terms: Cou, Ren, Cisqua, Rowen/Ro, Kea, Angel = アンゲル, song of oblivion, ...),
  `docs/style-reference.md`.

## Output: `font/labels.tsv`, written with your file-write tool
One line per key, in key order: `KEY<TAB>Japanese label<TAB>katakana reading or -<TAB>English`.
- English: title case, plain ASCII, no quotes needed; at most 94 px in the game font (roughly 16-19 characters;
  capitals and m/w are wide). Never abbreviate (no "&", "Atk", "Lv"); choose a shorter wording instead.
- Combo names: when the reading is an English loanword, use that English ("Triangle", "Red Lynx"); when it is a
  Japanese reading, translate the kanji meaning into a punchy skill name. Keep puns/jokes working ("お宝頂戴！" =
  "Treasure Grab!"-style). Keep "!" / "?" where the label has them.
- Items (I keys): use exactly the English already given for the matching string in script/sys.json if it exists;
  otherwise translate and report it as `ITEM: key - English` so the text can be matched.

## Validate
`python -X utf8 tools/gfx.py label-check font/labels.tsv` until it prints OK.
`python -X utf8 tools/gfx.py label-preview work/labels/preview.png` renders your English labels; look at it.

## Report (reply with only this)
Entry count; then `UNSURE: key - note` lines (unreadable kanji, guessed meanings) and `ITEM:` lines.
