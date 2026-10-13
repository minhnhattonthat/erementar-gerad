"""Text lint over script/*.json (run by tools/check.py). Prints errors and a count; exit 1 on any error.

Per translated entry: printable ASCII only, no leftover Japanese, fits its box (tools/fit.py), no glossary
'Avoid' spelling. Glossary terms whose English is missing are summarised in one warning line.
"""
import json, re, sys
import fit, romlib

ROOT = romlib.ROOT


def glossary():
    """[(jp, en, [avoid...])] from the tables in glossary.md."""
    rows = []
    for line in (ROOT / 'glossary.md').read_text('utf-8').splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) >= 5 and fit.JP_RE.search(cells[0]) and cells[1] and cells[1] != 'EN':
            avoid = [a.strip() for a in cells[4].split(',') if a.strip()]
            rows.append((cells[0], cells[1], avoid))
    return rows


def check_entry(e, en, gloss):
    errs, warns = [], []
    bad = sorted({c for c in en if c != '\n' and not (0x20 <= ord(c) < 0x7F)})
    if bad:
        errs.append(f'non-ASCII {"".join(bad)!r}')
    if fit.JP_RE.search(en):
        errs.append('Japanese left in en')
    if not bad:
        _, err = fit.layout(e, en)
        if err:
            errs.append(err)
    for jp, eng, avoid in gloss:
        for a in avoid:
            if re.search(r'\b' + re.escape(a) + r'\b', en):
                errs.append(f'glossary: "{a}" -> use "{eng}"')
        if jp in e['jp'] and eng.split(' (')[0] not in en:
            warns.append(f'{jp} -> {eng}')
    return errs, warns


def main():
    gloss = glossary()
    nerr, nwarn, done, total = 0, 0, 0, 0
    for p in sorted(romlib.SCRIPT_DIR.glob('*.json')):
        for e in json.loads(p.read_text('utf-8')):
            if fit.form(e) != 'keep':
                total += 1
            if e.get('en') is None:
                continue
            done += 1
            errs, warns = check_entry(e, e['en'], gloss)
            for x in errs:
                print(f"{p.name} {e['id']}: {x}")
            nerr += len(errs)
            nwarn += len(warns)
    print(f'lint: {done}/{total} translated, {nerr} errors, {nwarn} glossary terms not used verbatim (warning)')
    sys.exit(1 if nerr else 0)


if __name__ == '__main__':
    main()
