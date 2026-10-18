# Erementar Gerad (GBA) English translation

Skill: translate-retro-game (Claude Code plugin translate-retro-game@retro-translation).
Read it before ROM, text or QA work. `$S` below = `~/.claude/plugins/marketplaces/retro-translation/skills/translate-retro-game/scripts`.

## Commands (repo root; `python`, never `python3`)
- Check:   `python -X utf8 tools/check.py` (unittest + lint; the pre-commit hook runs this)
- Dump:    `python -X utf8 tools/dump.py` (refuses to overwrite; `--force` keeps en/notes)
- Build:   `python -X utf8 tools/build.py [--marker | --identity] [--qa ID=TEXT]` -> build/eg_en.gba
- Smoke:   `python -X utf8 $S/emu.py build/eg_en.gba --out work/qa/smoke --frames 1800 --shot-every 150 --sheet --smoke --timeout 120`
- Intro route (title -> first dialogue -> map menu): `--route-str "1500 -;6 start;120 -;6 a;120 -;6 a;120 -" --frames 3800 --mash 60 --mash-key a`
- Release: `python -X utf8 tools/release.py 0.9-beta` (check, build, smoke, jp_left, BPS verify, zip in release/;
  local only - never publish without the user)
- Graphics: tools/gfx.py (tags, labels, tabs, plates, badges, enemy tags, label-check/preview),
  tools/screens.py (LZ77 full-screen pictures: export/redraw), tools/lz77.py, tools/bgrender.py

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
- Also done: info headers, badges, status labels, battle plates, enemy tags, battle tutorial pages, title logo.
  v0.9-beta packaged (release/, gitignored). 2026-10-19 v0.9.1-beta: ELEMENTAL GELADE logo + subtitle,
  choice rows (16-cell buffer, width centring, lint CHOICE_W), list-menu centring, menu newline fix
  (Yes/No), battle result boxes, map place names (gfx.map_name_patches). QA state: work/states/en_choice_first.mss.
- Next: QA past the first battle (need a battle fast-forward: tools/lua/strong.lua pins the party record but the
  battle uses its own copy - find it), check choice/shop/arena/credits boxes in-game, docs/re/graphics.md rows
  10-11 (orange pool plates, tiny katakana font: find where shown), Minors polish pass (docs/review-log.md).
- QA routes: tools/routes/to_forest.txt (first scene), to_items.txt (item menu). Battles are long: find enemy HP
  in RAM for a fast-forward probe. Debug menu: tools/lua/debugmenu.lua.
- Workflow notes: translator/reviewer briefs in docs/; batches via tools/batches.py; term decisions in glossary.md.
