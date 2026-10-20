# Elemental Gelade: The Sealed Song English translation

Unofficial English fan translation of **Erementar Gerad: Tozasareshi Uta** (Game Boy Advance, Tomy, 2005): the source
text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## What's translated

- All story dialogue, menus, items, skill descriptions, shop and arena text, and the staff credits.
- Graphics text: title logo, dialogue name tags, battle name plates and result screen, enemy names, skill/attack/item
  banners, menu tabs, info-box labels, battle tutorial pages and world-map place names.
- A variable-width English font (two letters per game glyph) gives about 35 letters per line.
- Names follow the English anime release (*Elemental Gelade*); honorifics are kept.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `font/` | English fonts, name-tag font, graphics label text, title logo art. |
| `asm/` | Engine hooks (armips): pair-glyph VWF, menu and choice layout. |
| `tools/` | Python build chain: dump, build, graphics, lint, release. |
| `tests/` | unittest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/` | Translator/reviewer briefs, review log, style reference. |
| `CLAUDE.md` | Instructions for coding agents. |

## Build your own patched ROM

Needs Python 3.12+ with Pillow, armips in `tools/armips/`, and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/erementar-gerad
cd erementar-gerad
# copy your dump to: rom/2047 - Erementar Gerad (J)(Supplex).gba
#   (8388608 bytes, CRC32 8C1AFCA4, SHA-1 8c005e02b64ccf07de5905311db68983b0a3b76d)
python -X utf8 tools/build.py                          # -> build/eg_en.gba
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Tomy's and is included only so the
translation can be checked against it. Erementar Gerad is (c) Tomy / Jupiter; this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
