# Translation reviewer brief - Erementar Gerad (GBA)

You review batches of a JP->EN fan translation. Read-only: no edits, no git, no subagents. Mechanical validity
(ids, ASCII, box width, glossary 'Avoid' spellings) is already enforced by the check tool - judge translation quality.
Repo root: H:/translation/erementar-gerad.

## Inputs
- Pairs files `work/tl/<batch>.pairs.txt`: each entry is `>> id | speaker` / `JP:` / `EN:`; `(context)` lines are
  neighbours from other batches. Read ALL of each file, in passes if large. Speaker tags can be wrong on choice
  menus (the player's options carry the previous speaker's tag).
- `glossary.md` (rulings at the top, then term tables and "Decisions from earlier batches"),
  `docs/style-reference.md`.

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly; honorifics kept (-san/-chan/-kun/-sama, "Senpai"); voices per the
  style reference (Coud casual, Ren gentle/brief, Cisqua brisk and money-minded, Rowen polite, Kea sassy, Kansai
  speakers folksy).
- Things players catch that reviewers miss: jokes/wordplay losing their punch; ordinal suffix errors ("1th");
  abbreviated names or terms; stock phrases that read awkwardly in English; a sentence split across two boxes that
  no longer reads in sequence.
- Naturalness: would a fan-translation reader stumble?

## Report (reply with only this)
### <batch>
#### Critical (meaning reversed, wrong speaker/addressee, broken sense)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, lost joke)
#### Minor (style - deferred to one polish pass; list at most 10)
Each: `id - JP gist - problem - suggested EN` (suggested EN must stay about the same length or shorter).
### Assessment
Approved | Needs fixes - one sentence why.
