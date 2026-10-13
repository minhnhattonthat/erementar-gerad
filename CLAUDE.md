# Erementar Gerad (GBA) English translation

Skill: translate-retro-game (H:/translation/erementar-gerad/.claude/skills/translate-retro-game/SKILL.md).
Read it before ROM, text or QA work. `$S` below = `.claude/skills/translate-retro-game/scripts`.

## Commands (repo root; `python`, never `python3`)
- Check:   `python -X utf8 tools/check.py` (unittest + lint; the pre-commit hook runs this)
- Smoke:   `python -X utf8 $S/emu.py <rom> --out work/qa/smoke --frames 1800 --shot-every 150 --sheet --smoke --timeout 120`
- Build / release: not yet written.

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

## Status
- Done: Step 0; recon of encoding, pointer slots, sprite-glyph renderer (docs/re/).
- Next: extractor + roundtrip/coverage tests; engine spike (2 letters per cell, variable advance); marker build.
