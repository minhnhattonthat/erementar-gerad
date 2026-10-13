# Erementar Gerad (GBA) English translation

Skill: translate-retro-game (H:/translation/erementar-gerad/.claude/skills/translate-retro-game/SKILL.md).
Read it before ROM, text or QA work. `$S` below = `.claude/skills/translate-retro-game/scripts`.

## Commands (repo root; `python`, never `python3`)
- Check:   `python -X utf8 tools/check.py` (unittest + lint; the pre-commit hook runs this)
- Dump:    `python -X utf8 tools/dump.py` (refuses to overwrite; `--force` keeps en/notes)
- Build:   `python -X utf8 tools/build.py [--marker | --identity] [--qa ID=TEXT]` -> build/eg_en.gba
- Smoke:   `python -X utf8 $S/emu.py build/eg_en.gba --out work/qa/smoke --frames 1800 --shot-every 150 --sheet --smoke --timeout 120`
- Intro route (title -> first dialogue -> map menu): `--route-str "1500 -;6 start;120 -;6 a;120 -;6 a;120 -" --frames 3800 --mash 60 --mash-key a`
- Release: not yet written.

## Paths
- JP ROM `rom/2047 - Erementar Gerad (J)(Supplex).gba` (gitignored). Mesen 2.2.1 lives directly in `tools/`
  (Mesen.exe + Firmware/gba_bios.bin; gitignored): **QA in Mesen** (user ruling). armips `tools/armips/`.
  QA output `work/qa/`, savestates `work/states/`. Our code: `tools/*.py`, `tools/lua/`, `tests/`.
- RE notes: `docs/re/README.md`. Glossary + rulings: `glossary.md`.

## Rulings
- Edit source files only with the file-edit tool. Honorifics kept (hyphenated), official anime English names
  else Hepburn, credits English, all graphics text in scope, no abbreviations. Pre-approved: report at the end.
- Mesen: `tools/settings.json` needs `AllowIoOsAccess: true` (set) or runs hang to timeout.
- Another project's Mesen may be running (monster-guardians); don't kill processes you didn't start.

## Status (2026-10-14)
- Done: engine (pair-glyph VWF, 212 px dialogue lines), all 8344 strings translated + reviewed (Importants fixed;
  Minors queued in docs/review-log.md for one polish pass), name tags, 267 skill/attack/item labels
  (font/labels.tsv), menu tabs. jp_left on build: 0 reachable Japanese text.
- Next: UI graphics pieces (docs/re/graphics.md rows 5-10: info headers 回復/攻撃/スピード, badges 単体/全体, status
  labels, battle name plates, にげる/アイテム, title logo); measure choice/label menus in-game; polish pass; release.
- QA routes: tools/routes/to_forest.txt (first scene), to_items.txt (item menu). Battles are long: find enemy HP
  in RAM for a fast-forward probe. Debug menu: tools/lua/debugmenu.lua.
- Workflow notes: translator/reviewer briefs in docs/; batches via tools/batches.py; term decisions in glossary.md.
