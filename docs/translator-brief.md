# Translator brief - Erementar Gerad (GBA, Tomy/Jupiter 2005)

You translate part of the Japanese script of the GBA game *Erementar Gerad: Tozasareshi Uta* into English for a fan
patch. A light comic adventure/RPG based on the anime: Coud (Cou) and the Edel Raid Ren travel with Arc Aile officer
Cisqua, Rowen and his Edel Raid Kea toward the floating city Edel Garden; this game is set around the port town Porto
Galeon. Work only on the batch named in your dispatch. Do all translation yourself; do not dispatch subagents.
Repo root: H:/translation/erementar-gerad (run commands from there).

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `work/tl/<batch>.terms.txt` - binding glossary rows for this batch (`glossary.md` has the full table + rulings).

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`
- speaker: who says it, when known (from the game's portrait data; may be blank or a description - infer from context).
- form: `dlg` = dialogue box; `label` = short menu item / place name / talk option / topic; `sys` = system or menu text.
- limit: `3x212px` for dlg = up to 3 lines of 212 px (about 100-105 characters of English in total; the last line
  holds ~2 fewer words). label/sys: the soft target in px is the Japanese width; about 2 English characters per
  Japanese character fit. Keep labels short; they sit in narrow menus.
- ` / ` separates the lines of one box in the Japanese. Translate the box as one utterance.
- Lines are in story order; use neighbours for context. A run of 2-4 short lines with the same speaker right after a
  question is often a choice menu (the player's options) - keep each option short and parallel.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`, `--`; no tabs inside
the English, no Japanese or fullwidth characters, no `\uXXXX`. Do NOT insert line breaks: the build wraps each box
itself. (Exception: credits/lists where the Japanese ` / ` separates fields such as "Role / Name" - write `\n` there.)

## Validate
Run `python -X utf8 tools/batches.py check <batch>` and fix every reported id until it prints OK.
To see how one line wraps: `python -X utf8 tools/fit.py "English text" [--form dlg|label|sys]`.
If a dlg line can't fit 3x212px without losing meaning, tighten the wording (cut filler, not content); if still
impossible, keep the meaning and report it as `LONG: id`.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese
  doesn't state; don't summarise or skip. Adapt wordplay so the joke still lands (no translator notes).
- Use names and terms exactly as in the glossary. Never abbreviate names or terms to fit.
- Honorifics KEPT, hyphenated: -san, -chan, -kun, -sama (クード様 = "Coud-sama"); 先輩 = "Senpai".
- Punctuation: 「」 -> "...", 『』 -> "...", …/・・・ -> `...`, ！？ -> `?!`, ～ -> `~` only when playful.
- Numbers as digits: "527 Ganee". Never glue a suffix onto a number you don't see ("1st" etc.).
- Menu/label strings: title case for menu commands and place names ("Town Gate", "Use"), sentence case for messages.
- Character voices: see style-reference (Coud casual/brash, Ren gentle and brief, Cisqua brisk and money-minded,
  Rowen polite, Kea sassy; Kansai-dialect speakers = folksy "ya / ain't / -in'", no phonetic dialect spelling).

## Notes from earlier batches
- Speaker tags on choice menus are the previous speaker's; options are usually Coud's - judge from context.
- Song lyrics and React chants are translated (see glossary decisions), never romanised.
- Terms that drifted in wave 1 and are now fixed in the glossary: 黒集団 = "the Black Group", ヴォルクス = "Volks",
  ヴォル君 = "Vol-kun", ナスカム = "Nascam". The check tool rejects the old variants.
- A sentence split across two boxes: keep the split, make box 1 end naturally mid-sentence (comma/"and").
- Choice options: sentence case ("Hold hands", "Run for it"), short and parallel.
- React がとける/とかれる = "comes undone" (not "broken"). 港 alone = "harbor". "All right", never "Alright".
- "you know" as a sentence tag belongs to Chiruru only; don't give it to Kea or others. Dropped g's ("nothin'")
  belong to the Kansai-dialect speakers only.
- No "&" / "co." / abbreviations in labels or choices: if a choice won't fit its soft target, report LONG.
- Chiruru's のヨ tic -> "you know" at most once per box, and not every box.
- Japanese puns: keep the joke working (reviewers flagged a lost ふとっぱら "fat belly" pun and a マクラ/イクラ swap
  mistranslated as "bedding/herring"); get the literal items right first, then adapt.
- Lines repeated word-for-word from an earlier scene (flashbacks, other branches): reuse that English if you can
  find it with grep in script/*.json ("en" fields).

## Consistency
Never edit `glossary.md` or any file except your own `work/tl/<batch>.out.tsv`. For a recurring name or term not in
the glossary, pick a form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
